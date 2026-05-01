"""
Phase 1 — Listing scraper.

Paginates through the job listing and pushes new job detail URLs
into the ScrapeJob queue table.  Stops early when a full page of
URLs already exists in the DB (incremental scraping).
"""
import logging
from urllib.parse import urljoin, urlparse, urlencode, parse_qs, urlunparse

from .config import SiteConfig
from .http_client import ScraperError, fetch

logger = logging.getLogger(__name__)


def _build_listing_url(cfg: SiteConfig, page: int) -> str:
    base = cfg.base_url.rstrip("/") + cfg.listing_path
    return f"{base}?{cfg.pagination_param}={page}"


def _extract_card_urls(soup, cfg: SiteConfig) -> list[str]:
    """
    Return deduplicated absolute detail URLs found on a listing page.

    staff.am is a React Native Web app — CSS class names are hashed and
    unstable.  Instead, we rely on stable HTML attributes:
      - Job title links have target="_blank" and href starting with /en/jobs/
      - "View more" links for the same job use the same href but no target attr
    Collecting only target="_blank" anchors and deduplicating gives us exactly
    one URL per job card.
    """
    seen: set[str] = set()
    urls: list[str] = []
    for link in soup.find_all("a", target="_blank"):
        href = link.get("href", "").strip()
        if not href.startswith("/en/jobs/"):
            continue
        absolute = urljoin(cfg.base_url, href)
        if absolute not in seen:
            seen.add(absolute)
            urls.append(absolute)
    return urls


def run_listing_phase(cfg: SiteConfig, max_pages: int | None = None) -> int:
    """
    Paginate through the listing and enqueue new job URLs.

    Returns the number of NEW URLs added to the queue.
    Stops early if an entire page's URLs are already in the DB.
    """
    from scraper.models import ScrapeJob

    ceiling = max_pages if max_pages is not None else cfg.max_pages
    new_count = 0

    for page in range(1, ceiling + 1):
        url = _build_listing_url(cfg, page)
        logger.info("Listing page %d: %s", page, url)

        try:
            soup = fetch(url, cfg)
        except ScraperError as exc:
            logger.error("Failed to fetch listing page %d: %s", page, exc)
            break

        page_urls = _extract_card_urls(soup, cfg)
        if not page_urls:
            logger.info("No job cards found on page %d — stopping pagination", page)
            break

        logger.info("Found %d job cards on page %d", len(page_urls), page)

        page_new = 0
        for job_url in page_urls:
            _, created = ScrapeJob.objects.get_or_create(url=job_url)
            if created:
                page_new += 1

        new_count += page_new
        logger.info("Page %d: %d new URLs enqueued (%d already known)", page, page_new, len(page_urls) - page_new)

        # Early stop: full page already known → no need to go further
        if page_new == 0:
            logger.info("All URLs on page %d already in DB — stopping early", page)
            break

    logger.info("Listing phase complete: %d new URLs total", new_count)
    return new_count
