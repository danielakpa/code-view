"""Database models for the CodeView Community."""

from django.conf import settings
from django.db import models


class Post(models.Model):
    """A post shared in the public community."""

    # The developer who published the post.
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_posts",
    )

    # Community posts do not require titles.
    content = models.TextField()

    # Record when the post was published.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Post by {self.author}"


class Comment(models.Model):
    """A comment underneath a community post."""

    # The post being discussed.
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    # The developer who wrote the comment.
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    # The comment message.
    content = models.TextField(max_length=2000)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author}"


class Like(models.Model):
    """Record which developer liked which post."""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="likes",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    class Meta:
        # Prevent one developer from liking the same post twice.
        constraints = [
            models.UniqueConstraint(
                fields=["post", "user"],
                name="unique_community_post_like",
            )
        ]

    def __str__(self):
        return f"{self.user} liked post {self.post_id}"