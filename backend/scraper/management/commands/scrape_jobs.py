"""
Django management command for running the job scraper.

Usage:
    python manage.py scrape_jobs                      # full run (listing + detail)
    python manage.py scrape_jobs --phase listing      # only enqueue new URLs
    python manage.py scrape_jobs --phase detail       # only process pending URLs
    python manage.py scrape_jobs --max-pages 3        # limit listing pages (useful for testing)
    python manage.py scrape_jobs --batch-size 10      # detail batch size
    python manage.py scrape_jobs --retry-failed       # re-queue failed scrape jobs
"""
import logging

from django.core.management.base import BaseCommand

from scraper.services.config import STAFF_AM
from scraper.services.http_client import close_driver
from scraper.services.listing_scraper import run_listing_phase
from scraper.services.detail_scraper import run_detail_phase

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Scrape job listings from staff.am and save to the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--phase",
            choices=["listing", "detail", "all"],
            default="all",
            help="Which phase to run (default: all)",
        )
        parser.add_argument(
            "--max-pages",
            type=int,
            default=None,
            help="Maximum listing pages to fetch (overrides config)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=20,
            help="Number of detail pages to process per batch (default: 20)",
        )
        parser.add_argument(
            "--retry-failed",
            action="store_true",
            help="Reset failed ScrapeJob rows to PENDING before running",
        )

    def handle(self, *args, **options):
        from scraper.models import ScrapeJob

        cfg   = STAFF_AM
        phase = options["phase"]

        if options["retry_failed"]:
            count = ScrapeJob.objects.filter(status=ScrapeJob.Status.FAILED).update(
                status=ScrapeJob.Status.PENDING, attempts=0, error=""
            )
            self.stdout.write(self.style.WARNING(f"Reset {count} failed jobs to PENDING"))

        if phase in ("listing", "all"):
            self.stdout.write("── Phase 1: listing scraper ──")
            first_url = (
                f"{cfg.base_url.rstrip('/')}{cfg.listing_path}"
                f"?{cfg.pagination_param}=1"
            )
            self.stdout.write(f"  First URL: {first_url}")
            new_urls = run_listing_phase(cfg, max_pages=options["max_pages"])
            self.stdout.write(self.style.SUCCESS(f"Enqueued {new_urls} new job URLs"))

        if phase in ("detail", "all"):
            self.stdout.write("── Phase 2: detail scraper ──")
            saved = run_detail_phase(cfg, batch_size=options["batch_size"])
            self.stdout.write(self.style.SUCCESS(f"Saved {saved} jobs to database"))

        pending = ScrapeJob.objects.filter(status=ScrapeJob.Status.PENDING).count()
        failed  = ScrapeJob.objects.filter(status=ScrapeJob.Status.FAILED).count()
        done    = ScrapeJob.objects.filter(status=ScrapeJob.Status.DONE).count()
        self.stdout.write(f"Queue: {done} done | {pending} pending | {failed} failed")

        close_driver()
