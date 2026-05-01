"""
Phase 2 — Detail scraper.

Processes pending ScrapeJob rows in batches: fetches each job detail page,
extracts all fields, and upserts into Company / Job / JobSkill models.
"""
import logging
import random
import re
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from .config import SiteConfig
from .http_client import ScraperError, fetch
from .skill_extractor import extract_skills

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _text(soup, selector: str) -> str:
    """Return stripped text of the first matching element, or empty string."""
    if not selector:
        return ""
    el = soup.select_one(selector)
    return el.get_text(separator=" ", strip=True) if el else ""


def _parse_salary(raw: str) -> tuple[Decimal | None, Decimal | None]:
    """
    Parse a salary string into (min, max) Decimal pair.

    Handles patterns like:
        "1,500 – 2,500 AMD"
        "$3,000 - $5,000"
        "Up to 4000"
        "From 2000 USD"
        "3000"
    Returns (None, None) when no numeric value found.
    """
    if not raw:
        return None, None

    # Remove currency symbols and words, normalise separators
    cleaned = re.sub(r"[AMD$€£₽\s]", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r",", "", cleaned)

    numbers = re.findall(r"\d+(?:\.\d+)?", cleaned)
    if not numbers:
        return None, None

    try:
        if len(numbers) == 1:
            val = Decimal(numbers[0])
            # "Up to X" → max only; "From X" → min only
            if re.search(r"\bup\s*to\b", raw, re.IGNORECASE):
                return None, val
            if re.search(r"\bfrom\b", raw, re.IGNORECASE):
                return val, None
            return val, val
        return Decimal(numbers[0]), Decimal(numbers[1])
    except InvalidOperation:
        return None, None


_REMOTE_RE = re.compile(r"\bremote\b", re.IGNORECASE)
_HYBRID_RE = re.compile(r"\bhybrid\b", re.IGNORECASE)


def _parse_job_type(raw: str) -> str:
    if _REMOTE_RE.search(raw):
        return "remote"
    if _HYBRID_RE.search(raw):
        return "hybrid"
    return "onsite"


# ── Main phase function ───────────────────────────────────────────────────────

def run_detail_phase(cfg: SiteConfig, batch_size: int = 20) -> int:
    """
    Process all PENDING ScrapeJob rows in batches.
    Returns the total number of jobs successfully saved.
    """
    from scraper.models import ScrapeJob
    from jobs.models import Company, Job, JobSkill

    total_saved = 0
    processed = 0

    while True:
        batch = list(
            ScrapeJob.objects
            .filter(status=ScrapeJob.Status.PENDING, attempts__lt=3)
            .order_by("created_at")[:batch_size]
        )
        if not batch:
            break

        # Randomize processing order to avoid predictable crawl patterns.
        random.shuffle(batch)

        for scrape_job in batch:
            scrape_job.attempts += 1
            scrape_job.save(update_fields=["attempts"])

            logger.info("Processing [%d/~?] %s", processed + 1, scrape_job.url)

            try:
                saved = _process_detail(scrape_job.url, cfg)
                if saved:
                    scrape_job.status       = ScrapeJob.Status.DONE
                    scrape_job.processed_at = timezone.now()
                    scrape_job.error        = ""
                    total_saved += 1
                else:
                    scrape_job.status = ScrapeJob.Status.FAILED
                    scrape_job.error  = "No usable data extracted"
            except ScraperError as exc:
                logger.warning("Scrape error for %s: %s", scrape_job.url, exc)
                scrape_job.status = ScrapeJob.Status.FAILED
                scrape_job.error  = str(exc)
            except Exception as exc:
                logger.error("Unexpected error for %s: %s", scrape_job.url, exc, exc_info=True)
                scrape_job.status = ScrapeJob.Status.FAILED
                scrape_job.error  = f"{type(exc).__name__}: {exc}"

            scrape_job.processed_at = timezone.now()
            scrape_job.save(update_fields=["status", "attempts", "error", "processed_at"])
            processed += 1

    logger.info("Detail phase complete: %d saved, %d processed", total_saved, processed)
    return total_saved


def _process_detail(url: str, cfg: SiteConfig) -> bool:
    """
    Fetch one detail page, extract fields, upsert into DB.
    Returns True if a Job was saved, False if critical data was missing.
    """
    from jobs.models import Company, Job, JobSkill

    soup = fetch(url, cfg)

    title   = _text(soup, cfg.detail_title_sel)
    company = _text(soup, cfg.detail_company_sel)

    if not title or not company:
        logger.warning("Missing title or company on %s — skipping", url)
        return False

    description  = _text(soup, cfg.detail_description_sel)
    requirements = _text(soup, cfg.detail_requirements_sel)
    location     = _text(soup, cfg.detail_location_sel)
    salary_raw   = _text(soup, cfg.detail_salary_sel)
    jobtype_raw  = _text(soup, cfg.detail_jobtype_sel)

    salary_min, salary_max = _parse_salary(salary_raw)
    job_type = _parse_job_type(jobtype_raw or location)

    # Skills: prefer structured tags; fall back to extracting from text
    if cfg.detail_skills_sel:
        skill_names = [
            el.get_text(strip=True)
            for el in soup.select(cfg.detail_skills_sel)
            if el.get_text(strip=True)
        ]
    else:
        skill_names = []

    if not skill_names:
        skill_names = extract_skills(f"{description} {requirements}")

    # Normalise
    skill_names = [s.strip().lower().title() for s in skill_names if s.strip()]

    with transaction.atomic():
        company_obj, _ = Company.objects.get_or_create(
            name=company.strip(),
            defaults={"location": location},
        )

        job_obj, created = Job.objects.update_or_create(
            source_url=url,
            defaults={
                "company":      company_obj,
                "title":        title.strip()[:255],
                "description":  description,
                "requirements": requirements,
                "location":     location[:255],
                "job_type":     job_type,
                "salary_min":   salary_min,
                "salary_max":   salary_max,
                "is_active":    True,
            },
        )

        # Rebuild skills atomically
        JobSkill.objects.filter(job=job_obj).delete()
        if skill_names:
            JobSkill.objects.bulk_create([
                JobSkill(job=job_obj, skill_name=name[:100])
                for name in skill_names[:30]  # cap at 30 skills per job
            ])

    action = "created" if created else "updated"
    logger.info("%s job: %s @ %s (%d skills)", action, title, company, len(skill_names))
    return True
