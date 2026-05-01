"""
Django management command for cleaning up expired or stale jobs.

Usage:
    python manage.py cleanup_jobs                  # deactivate all expired/stale jobs
    python manage.py cleanup_jobs --dry-run        # report counts without making changes
    python manage.py cleanup_jobs --days 60        # use 60-day staleness threshold
    python manage.py cleanup_jobs --hard-delete    # permanently delete instead of deactivating

Rules:
    1. Jobs with end_date < today  → deactivated (deadline passed)
    2. Jobs with no end_date and created_at older than --days → deactivated (too old)
"""
import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Deactivate (or delete) expired and stale jobs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be cleaned up without making any changes",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Staleness threshold in days for jobs with no end_date (default: 30)",
        )
        parser.add_argument(
            "--hard-delete",
            action="store_true",
            help="Permanently delete jobs instead of marking them inactive",
        )

    def handle(self, *args, **options):
        from jobs.models import Job

        dry_run     = options["dry_run"]
        days        = options["days"]
        hard_delete = options["hard_delete"]

        now    = timezone.now()
        today  = now.date()
        cutoff = now - timedelta(days=days)

        # Rule 1: application deadline has passed
        expired_qs = Job.objects.filter(is_active=True, end_date__lt=today)
        expired_count = expired_qs.count()

        # Rule 2: no deadline, job was created more than `days` ago
        stale_qs = Job.objects.filter(
            is_active=True,
            end_date__isnull=True,
            created_at__lt=cutoff,
        )
        stale_count = stale_qs.count()

        total = expired_count + stale_count

        action_label = "delete" if hard_delete else "deactivate"
        self.stdout.write(f"Expired (end_date < {today}):       {expired_count}")
        self.stdout.write(f"Stale   (>{days}d old, no end_date): {stale_count}")
        self.stdout.write(f"Total to {action_label}:               {total}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no changes made"))
            return

        if total == 0:
            self.stdout.write(self.style.SUCCESS("Nothing to clean up"))
            return

        with transaction.atomic():
            if hard_delete:
                # CASCADE handles JobSkill and JobMatch rows automatically.
                expired_qs.delete()
                stale_qs.delete()
            else:
                expired_qs.update(is_active=False)
                stale_qs.update(is_active=False)

        logger.info(
            "cleanup_jobs: %s %d expired + %d stale = %d total",
            action_label, expired_count, stale_count, total,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"{action_label.capitalize()}d {total} jobs "
                f"({expired_count} expired, {stale_count} stale)"
            )
        )
