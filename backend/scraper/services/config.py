"""
SiteConfig — all site-specific settings in one place.

HOW TO FILL IN SELECTORS
─────────────────────────
1. Open the target site in Chrome.
2. Press F12 → Elements tab.
3. Hover over the element you want to target, right-click → "Copy selector".
4. Replace the VERIFY placeholder with that selector.
5. Repeat for each field on both the listing page and a detail page.
"""
from dataclasses import dataclass, field


@dataclass
class SiteConfig:
    # ── Site ──────────────────────────────────────────────────────────────────
    base_url:         str
    listing_path:     str   # e.g. "/en/jobs"
    pagination_param: str   # URL query param name, e.g. "page"
    max_pages:        int   # safety ceiling to prevent infinite loops

    # ── Listing page selectors ────────────────────────────────────────────────
    card_selector:      str   # CSS selector that wraps ONE job card
    card_link_attr:     str   # attribute on the <a> tag that holds the URL (usually "href")
    card_link_selector: str   # CSS selector for the <a> tag inside a card
    card_title_sel:     str
    card_company_sel:   str
    card_location_sel:  str

    # ── Detail page selectors ─────────────────────────────────────────────────
    detail_title_sel:       str
    detail_company_sel:     str
    detail_description_sel: str
    detail_requirements_sel: str
    detail_skills_sel:      str   # empty string → extract via skill_extractor
    detail_salary_sel:      str   # empty string → no salary on page
    detail_location_sel:    str
    detail_jobtype_sel:     str

    # ── HTTP ──────────────────────────────────────────────────────────────────
    user_agent:    str
    request_delay: tuple    = (1.5, 4.5)   # kept for reference; fetch() uses these bounds
    timeout:       int      = 20            # Selenium wait timeout in seconds
    proxy:         str | None = None        # e.g. "http://user:pass@host:port"


# ─────────────────────────────────────────────────────────────────────────────
# staff.am configuration
#
# IMPORTANT: All selectors below are placeholders.
# You MUST verify and update each one by inspecting staff.am in browser DevTools.
#
# Quick steps:
#   1. Go to https://staff.am/en/jobs
#   2. F12 → Inspector → hover over a job card
#   3. Note the outer element's class (update card_selector)
#   4. Note the <a> link's class (update card_link_selector)
#   5. Note title / company / location element classes
#   6. Click a job → repeat for detail page selectors
# ─────────────────────────────────────────────────────────────────────────────

STAFF_AM = SiteConfig(
    base_url         = "https://staff.am",
    listing_path     = "/en/jobs",
    pagination_param = "page",
    max_pages        = 100,

    # ── Listing selectors ─────────────────────────────────────────────────────
    # staff.am uses React Native Web — CSS classes are hashed and unstable.
    # card_selector is used only as a Selenium wait condition; we wait until at
    # least one job link appears before parsing the page.
    card_selector      = 'a[href*="/en/jobs/"]',    # Selenium wait condition
    card_link_attr     = "href",
    card_link_selector = 'a[href*="/en/jobs/"]',    # unused by listing scraper
    card_title_sel     = "",                         # extracted during detail phase
    card_company_sel   = "",
    card_location_sel  = "",

    # ── Detail selectors (VERIFY in DevTools) ─────────────────────────────────
    detail_title_sel        = "h1.job-view__title",
    detail_company_sel      = ".job-view__company-name",
    detail_description_sel  = ".job-view__description",
    detail_requirements_sel = ".job-view__requirements",
    detail_skills_sel       = ".job-view__skill-tag",   # empty → parse from text
    detail_salary_sel       = ".job-view__salary",      # empty → no salary shown
    detail_location_sel     = ".job-view__location",
    detail_jobtype_sel      = ".job-view__work-type",

    # ── HTTP ──────────────────────────────────────────────────────────────────
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    request_delay = (1.5, 4.5),
    timeout       = 20,
    proxy         = None,
)
