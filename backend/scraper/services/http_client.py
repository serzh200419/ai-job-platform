"""
Selenium-based HTTP client (headful Chrome).

Anti-detection measures:
  - Random User-Agent rotation via CDP on every request
  - Extra HTTP headers injected (Accept, Accept-Language, Connection)
  - Short delay 1.5–4.5 s before every request
  - Long pause 10–25 s every 10–15 requests to break timing patterns
  - 3-attempt retry with exponential backoff (2 s / 5 s / 10 s)
  - Cloudflare challenge detection with 30 s grace period
  - Optional proxy (set cfg.proxy = "http://host:port")

Session reuse: one driver instance is shared for the entire scraping session.
Call close_driver() when done to shut the browser.
"""
import logging
import random
import re
import subprocess
import time

from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

import undetected_chromedriver as uc

from .config import SiteConfig

logger = logging.getLogger(__name__)


def _detect_chrome_version() -> int | None:
    """
    Return the installed Chrome major version number, or None if undetectable.
    Checks the Windows registry first, falls back to running 'chrome --version'.
    undetected_chromedriver uses this to download the matching ChromeDriver binary.
    """
    # Windows registry (most reliable on Windows)
    reg_keys = [
        r"HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon",
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Google\Chrome\BLBeacon",
        r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Google\Chrome\BLBeacon",
    ]
    for key in reg_keys:
        try:
            result = subprocess.run(
                ["reg", "query", key, "/v", "version"],
                capture_output=True, text=True, timeout=5,
            )
            m = re.search(r"(\d+)\.\d+\.\d+\.\d+", result.stdout)
            if m:
                ver = int(m.group(1))
                logger.info("Detected Chrome version from registry: %d", ver)
                return ver
        except Exception:
            pass

    # Fallback: ask Chrome directly
    try:
        result = subprocess.run(
            ["google-chrome", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        m = re.search(r"(\d+)\.\d+\.\d+", result.stdout)
        if m:
            return int(m.group(1))
    except Exception:
        pass

    logger.warning("Could not detect Chrome version — uc will use latest ChromeDriver")
    return None


class ScraperError(Exception):
    pass


class CloudflareBlockError(ScraperError):
    """Raised when Cloudflare challenge does not resolve after the grace period."""
    pass


# ── User-Agent pool ───────────────────────────────────────────────────────────

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
]

_ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9",
    "en-US,en;q=0.9,hy;q=0.6",
    "en-US,en;q=0.8,ru;q=0.6",
]

# ── Request pacing state ──────────────────────────────────────────────────────

_request_count:       int = 0
_next_long_pause_at:  int = random.randint(10, 15)

_driver: uc.Chrome | None = None

# Retry backoff schedule (seconds per attempt 1, 2, 3)
_RETRY_BACKOFF = (2, 5, 10)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _rotate_headers(driver: uc.Chrome) -> None:
    """Override UA and HTTP headers via CDP. Called before every navigation."""
    ua   = random.choice(_USER_AGENTS)
    lang = random.choice(_ACCEPT_LANGUAGES)
    try:
        driver.execute_cdp_cmd("Network.setUserAgentOverride", {
            "userAgent":      ua,
            "acceptLanguage": lang,
        })
        driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
            "headers": {
                "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": lang,
                "Connection":      "keep-alive",
            }
        })
    except Exception as exc:
        logger.debug("Header rotation skipped: %s", exc)
    logger.debug("Rotated UA to: %.80s", ua)


def _is_cloudflare_challenge(driver: uc.Chrome) -> bool:
    title  = driver.title.lower()
    source = driver.page_source.lower()
    return (
        "just a moment" in title
        or "attention required" in title
        or "cf-browser-verification" in source
        or "checking your browser" in source
    )


def _safe_to_hover(element) -> bool:
    try:
        return element.is_displayed() and element.size.get("height", 0) > 5
    except Exception:
        return False


def _safe_to_click(element) -> bool:
    """True only for inert elements that cannot trigger navigation or form submission."""
    try:
        if not element.is_displayed():
            return False
        tag = element.tag_name.lower()
        if tag in ("a", "button", "input", "select", "textarea", "form"):
            return False
        if element.get_attribute("href") or element.get_attribute("onclick"):
            return False
        return True
    except Exception:
        return False


def simulate_human_behavior(driver: uc.Chrome) -> None:
    """
    Simulate human-like interaction after a page load.

    Behaviour (total 2–6 s added):
      - Short reading pause
      - Gradual scroll down in random steps
      - 40 % chance of small scroll-back (re-reading gesture)
      - Mouse hover over 2–3 random visible elements
      - 15 % chance of a safe click on an inert element

    Entirely fail-safe: every action is wrapped so any exception is
    swallowed and scraping continues normally.
    """
    from selenium.webdriver.common.action_chains import ActionChains

    try:
        # Reading pause right after page loads
        time.sleep(random.uniform(0.5, 1.5))

        page_height = driver.execute_script("return document.body.scrollHeight") or 1000

        # Gradual scroll down
        scrolled  = 0
        target_px = min(random.randint(400, 1200), page_height // 2)
        while scrolled < target_px:
            step = random.randint(150, 500)
            driver.execute_script(f"window.scrollBy(0, {step})")
            scrolled += step
            time.sleep(random.uniform(0.25, 0.8))

        # Occasionally scroll back up a little (simulates re-reading)
        if random.random() < 0.4:
            driver.execute_script(f"window.scrollBy(0, -{random.randint(80, 220)})")
            time.sleep(random.uniform(0.2, 0.5))

        # Hover over a few random visible elements
        candidates = driver.find_elements(By.CSS_SELECTOR, "p, span, li, h2, h3, label")
        hoverable  = [e for e in candidates[:40] if _safe_to_hover(e)]
        for el in random.sample(hoverable, k=min(3, len(hoverable))):
            try:
                ActionChains(driver).move_to_element(el).perform()
                time.sleep(random.uniform(0.1, 0.35))
            except Exception:
                pass

        # ~15 % chance: click an inert element (span/p/li with no href or onclick)
        if random.random() < 0.15:
            click_pool = driver.find_elements(By.CSS_SELECTOR, "p, span, li")
            safe_els   = [e for e in click_pool[:30] if _safe_to_click(e)]
            if safe_els:
                try:
                    ActionChains(driver).move_to_element(random.choice(safe_els)).click().perform()
                    time.sleep(random.uniform(0.2, 0.5))
                except Exception:
                    pass

        # Brief final pause before parsing
        time.sleep(random.uniform(0.3, 0.8))

    except Exception as exc:
        logger.debug("simulate_human_behavior skipped: %s", exc)


# ── Public API ────────────────────────────────────────────────────────────────

def get_driver(cfg: SiteConfig) -> uc.Chrome:
    """Return the shared Chrome driver, creating it on first call."""
    global _driver
    if _driver is None:
        options = uc.ChromeOptions()
        options.add_argument(f"--user-agent={random.choice(_USER_AGENTS)}")
        options.add_argument("--start-maximized")
        options.add_argument("--no-first-run")
        options.add_argument("--no-service-autorun")
        options.add_argument("--password-store=basic")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")

        if cfg.proxy:
            options.add_argument(f"--proxy-server={cfg.proxy}")
            logger.info("Proxy configured: %s", cfg.proxy)

        chrome_ver = _detect_chrome_version()
        _driver = uc.Chrome(
            options=options,
            headless=False,
            version_main=chrome_ver,
        )

        # Give Chrome time to fully initialize before issuing CDP commands.
        time.sleep(2)

        try:
            _driver.execute_cdp_cmd("Network.enable", {})
        except Exception as exc:
            logger.warning("CDP Network.enable failed (non-fatal): %s", exc)

        logger.info("Chrome driver started (headful)")
    return _driver


def close_driver() -> None:
    """Quit the shared Chrome driver."""
    global _driver
    if _driver is not None:
        try:
            _driver.quit()
        except Exception:
            pass
        _driver = None
        logger.info("Chrome driver closed")


def fetch(url: str, cfg: SiteConfig, *, wait_selector: str | None = None) -> BeautifulSoup:
    """
    Navigate to *url* with the shared Chrome driver and return a BeautifulSoup
    of the rendered page source.

    Pacing:
      - 1.5–4.5 s random delay before every request
      - 10–25 s long pause every 10–15 requests (breaks timing patterns)

    Reliability:
      - Headers rotated via CDP before each navigation
      - 3 retries with exponential backoff on WebDriver failure
      - Cloudflare challenge detected; waits 30 s then raises CloudflareBlockError

    wait_selector: CSS selector to wait for before parsing (defaults to the
                   card_selector on listing pages, 'body' otherwise).
    """
    global _request_count, _next_long_pause_at

    _request_count += 1

    # Long pause every N requests to break temporal patterns
    if _request_count >= _next_long_pause_at:
        long_pause = random.uniform(10, 25)
        logger.debug(
            "Long anti-pattern pause %.1fs (request #%d)", long_pause, _request_count
        )
        time.sleep(long_pause)
        _next_long_pause_at = _request_count + random.randint(10, 15)

    # Normal per-request delay
    delay = random.uniform(1.5, 4.5)
    logger.debug("Sleeping %.1fs before %s", delay, url)
    time.sleep(delay)

    driver = get_driver(cfg)
    _rotate_headers(driver)

    logger.info("Navigating to: %s", url)

    # Navigation with retry + exponential backoff
    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            driver.get(url)
            last_exc = None
            break
        except WebDriverException as exc:
            last_exc = exc
            if attempt < 3:
                backoff = _RETRY_BACKOFF[attempt - 1]
                logger.warning(
                    "Navigation attempt %d/3 failed for %s — retrying in %ds: %s",
                    attempt, url, backoff, exc,
                )
                time.sleep(backoff)

    if last_exc:
        raise ScraperError(
            f"Navigation failed after 3 attempts for {url}: {last_exc}"
        ) from last_exc

    # Cloudflare challenge detection
    if _is_cloudflare_challenge(driver):
        logger.warning("Cloudflare challenge on %s — waiting 30 s for resolution", url)
        time.sleep(30)
        if _is_cloudflare_challenge(driver):
            raise CloudflareBlockError(f"Cloudflare block persists on {url}")

    selector = wait_selector or (
        cfg.card_selector
        if (url.endswith(cfg.listing_path) or cfg.pagination_param in url)
        else "body"
    )

    try:
        WebDriverWait(driver, cfg.timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
    except TimeoutException:
        logger.warning("Timed out waiting for '%s' on %s — parsing anyway", selector, url)

    simulate_human_behavior(driver)

    logger.debug("Fetched %s (%d chars)", url, len(driver.page_source))
    return BeautifulSoup(driver.page_source, "html.parser")
