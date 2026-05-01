import uuid

from django.conf import settings
from django.db import models


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions"
    )
    profile_summary = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Session {self.id} ({self.user.email})"


class ChatMessage(models.Model):
    class Sender(models.TextChoices):
        USER = "user", "User"
        AI = "ai", "AI"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=Sender.choices)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.sender}] {self.message[:60]}"


class LawDocument(models.Model):
    title       = models.CharField(max_length=500, blank=True)
    content     = models.TextField()
    embedding   = models.JSONField(default=list)
    chunk_index = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["chunk_index"]

    def __str__(self):
        return f"{self.title or 'LawDoc'} [{self.chunk_index}]"
