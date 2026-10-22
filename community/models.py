"""Database models for CodeView project groups."""

from django.conf import settings
from django.db import models


# ============================================================
# 1. PROJECT GROUP
# ============================================================

class ProjectGroup(models.Model):
    """Store developer collaboration groups."""

    name = models.CharField(max_length=100)

    description = models.TextField()

    # Developer who created the group.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_project_groups",
    )

    # False = public group; True = private group.
    is_private = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


# ============================================================
# 2. GROUP MEMBER
# ============================================================

class GroupMember(models.Model):
    """Store group memberships and member roles."""

    group = models.ForeignKey(
        ProjectGroup,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("member", "Member"),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="member",
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["group", "user"],
                name="unique_project_group_member",
            ),
        ]

    def __str__(self):
        return f"{self.user} in {self.group.name}"


# ============================================================
# 3. GROUP DISCUSSION
# ============================================================

class GroupDiscussion(models.Model):
    """Store discussions created inside project groups."""

    group = models.ForeignKey(
        ProjectGroup,
        on_delete=models.CASCADE,
        related_name="discussions",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_discussions",
    )

    title = models.CharField(max_length=200)

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


# ============================================================
# 4. GROUP DISCUSSION COMMENT
# ============================================================

class GroupDiscussionComment(models.Model):
    """Store comments underneath group discussions."""

    discussion = models.ForeignKey(
        GroupDiscussion,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    content = models.TextField(max_length=2000)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.username}"