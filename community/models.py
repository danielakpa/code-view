"""Database models for CodeView Community."""

from django.conf import settings
from django.db import models


class Post(models.Model):
    """Store a post published by a developer."""

    # The developer who created the post.
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_posts",
    )

    # The post's text or pasted code.
    content = models.TextField()

    # Date and time the post was created.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Post by {self.author}"


class Comment(models.Model):
    """Store comments underneath community posts."""

    # The post this comment belongs to.
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

    # Date and time the comment was created.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author}"


class Like(models.Model):
    """Record which developer liked a post."""

    # The post being liked.
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="likes",
    )

    # The developer who liked the post.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    class Meta:
        # Each developer can like a particular post only once.
        constraints = [
            models.UniqueConstraint(
                fields=["post", "user"],
                name="unique_community_post_like",
            ),
        ]

    def __str__(self):
        return f"{self.user} liked post {self.post_id}"

# ========================================
# PROJECT GROUP MODELS
# ========================================


class ProjectGroup(models.Model):
    """Store developer collaboration groups."""

    # The name of the project group.
    name = models.CharField(max_length=100)

    # Explain what the group is building.
    description = models.TextField()

    # The developer who created the group.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_project_groups",
    )

    # Public groups are discoverable.
    # Private groups require permission to join.
    is_private = models.BooleanField(default=False)

    # Record when the group was created.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    """Store developers who belong to a project group."""

    # The group the developer belongs to.
    group = models.ForeignKey(
        ProjectGroup,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    # The developer joining the group.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    # A member can be an admin or regular member.
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("member", "Member"),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="member",
    )

    # Record when the developer joined.
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevent duplicate membership.
        constraints = [
            models.UniqueConstraint(
                fields=["group", "user"],
                name="unique_project_group_member",
            ),
        ]

    def __str__(self):
        return f"{self.user} in {self.group.name}"