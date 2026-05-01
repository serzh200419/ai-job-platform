from django.db import models


class ScrapeJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        DONE    = "done",    "Done"
        FAILED  = "failed",  "Failed"

    url          = models.URLField(unique=True, max_length=2048)
    status       = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    attempts     = models.IntegerField(default=0)
    error        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.status}] {self.url}"
