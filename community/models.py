
"""Database models for CodeView Community."""

from django.conf import settings
from django.db import models


class Post(models.Model):
    # User who published the post.
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )

    # Community posts contain text or pasted code.
    content = models.TextField()

    # Automatically record when the post was created.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Newest posts appear first.
        ordering = ["-created_at"]

    def __str__(self):
        return f"Post by {self.author.username}"
