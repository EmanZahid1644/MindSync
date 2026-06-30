from django.db import models


class TopicResourceCache(models.Model):
    normalized_topic = models.CharField(max_length=255, unique=True)
    original_topic = models.CharField(max_length=255)
    resources_payload = models.JSONField(default=dict, blank=True)
    flashcards = models.JSONField(default=list, blank=True)
    source = models.CharField(max_length=20, default="gemini")
    hit_count = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Resource Cache: {self.original_topic}"
