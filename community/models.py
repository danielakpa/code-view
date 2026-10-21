from django.db import models
from django.contrib.auth.models import User


class Post(models.Model):
    # The user who created the post.
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts"
    )

    # The title of the programming post.
    title = models.CharField(max_length=200)

    # The question, explanation, or code shared.
    content = models.TextField()

    # Automatically save when the post was created.
    created_at = models.DateTimeField(auto_now_add=True)

    # Show the newest posts first.
    class Meta:
        ordering = ["-created_at"]

    # How the post appears in Django Admin.
    def __str__(self):
        return self.title