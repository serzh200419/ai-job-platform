import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class JobMatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="job_matches"
    )
    job = models.ForeignKey("jobs.Job", on_delete=models.CASCADE, related_name="matches")
    match_score = models.FloatField()
    reason = models.TextField(blank=True)
    calculated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "job")
        ordering = ["-match_score"]

    def __str__(self):
        return f"{self.user.email} → {self.job.title} ({self.match_score:.0%})"
