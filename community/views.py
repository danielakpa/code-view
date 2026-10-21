
"""Handle CodeView community posts, comments, likes, and project groups."""

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import (
    CommentForm,
    PostForm,
    ProjectGroupForm,
)
from .models import (
    GroupMember,
    Like,
    Post,
    ProjectGroup,
)


# ============================================================
# 1. COMMUNITY FEED
# ============================================================
# Purpose:
# Display community posts and allow logged-in developers
# to publish new posts.
#
# The feed shows:
# - Post content and author
# - Number of likes
# - Number of comments
# - Whether the current developer liked each post
# ============================================================

@login_required
def community(request):
    """Display community posts and handle new post submissions."""

    # Check whether the developer submitted a new post.
    if request.method == "POST":

        # Collect and validate the submitted information.
        form = PostForm(request.POST)

        if form.is_valid():

            # Create the post object without saving immediately.
            post = form.save(commit=False)

            # Assign the logged-in developer as the author.
            post.author = request.user

            # Save the post to PostgreSQL.
            post.save()

            # Redirect to prevent duplicate submissions on refresh.
            return redirect("community")

    else:

        # Display an empty form when opening the page.
        form = PostForm()

    # Retrieve posts, their authors, and related comments.
    posts = (
        Post.objects
        .select_related("author")
        .prefetch_related("comments__author")
        .annotate(
            likes_count=Count("likes", distinct=True),
            comments_count=Count("comments", distinct=True),
        )
    )

    # Retrieve IDs of posts liked by the logged-in developer.
    liked_post_ids = set(
        Like.objects
        .filter(user=request.user)
        .values_list("post_id", flat=True)
    )

    # Mark each post as liked or not liked by this developer.
    for post in posts:
        post.is_liked = post.id in liked_post_ids

    # Display the community template with its required data.
    return render(
        request,
        "community/community.html",
        {
            "form": form,
            "posts": posts,
            "comment_form": CommentForm(),
        },
    )


# ============================================================
# 2. COMMUNITY COMMENTS
# ============================================================
# Purpose:
# Allow logged-in developers to comment underneath posts.
#
# Each comment:
# - Belongs to a specific post
# - Has an author
# - Is saved in PostgreSQL
#
# After commenting, the post's comments section opens.
# ============================================================

@login_required
@require_POST
def add_comment(request, post_id):
    """Validate and save a comment underneath a community post."""

    # Find the requested post or return a 404 error.
    post = get_object_or_404(
        Post,
        id=post_id,
    )

    # Collect the comment submitted by the developer.
    form = CommentForm(request.POST)

    # Save only valid comments.
    if form.is_valid():

        # Prepare the comment without saving immediately.
        comment = form.save(commit=False)

        # Connect the comment to the correct post.
        comment.post = post

        # Record the logged-in developer as the author.
        comment.author = request.user

        # Save the comment in PostgreSQL.
        comment.save()

    # Return to the same post and open its comments.
    community_url = reverse("community")

    return redirect(
        f"{community_url}?comments={post.id}#post-{post.id}"
    )


# ============================================================
# 3. COMMUNITY LIKES
# ============================================================
# Purpose:
# Allow logged-in developers to like and unlike posts.
#
# First click:
# - Creates a Like record in PostgreSQL
# - Turns the Like button green
#
# Second click:
# - Removes the Like record
# - Returns the button to its normal color
# ============================================================

@login_required
@require_POST
def toggle_like(request, post_id):
    """Like or unlike an existing community post."""

    # Find the post or return a 404 error.
    post = get_object_or_404(
        Post,
        id=post_id,
    )

    # Create a like if the developer has not liked the post.
    like, created = Like.objects.get_or_create(
        post=post,
        user=request.user,
    )

    # If the like already existed, remove it.
    if not created:
        like.delete()

    # Return to the same post after liking or unliking.
    community_url = reverse("community")

    return redirect(
        f"{community_url}#post-{post.id}"
    )


# ============================================================
# 4. CREATE PROJECT GROUP
# ============================================================
# Purpose:
# Allow a logged-in developer to create a collaboration group.
#
# When a group is created:
# - The developer becomes the group owner
# - The group is saved in PostgreSQL
# - The owner is automatically registered as an admin
#
# A group can be public or private.
# ============================================================

@login_required
def create_group(request):
    """Create a project group and register its owner as an admin."""

    # Check whether the developer submitted the group form.
    if request.method == "POST":

        # Collect and validate the submitted group information.
        form = ProjectGroupForm(request.POST)

        if form.is_valid():

            # Keep group creation and owner membership together.
            # If either database operation fails, both are rolled back.
            with transaction.atomic():

                # Prepare the group without saving immediately.
                group = form.save(commit=False)

                # Assign the logged-in developer as group owner.
                group.owner = request.user

                # Save the group to PostgreSQL.
                group.save()

                # Automatically add the owner as a group admin.
                GroupMember.objects.create(
                    group=group,
                    user=request.user,
                    role="admin",
                )

            # Redirect to the group listing after successful creation.
            return redirect("groups")

    else:

        # Display an empty form when opening the page.
        form = ProjectGroupForm()

    # Display the group creation page.
    return render(
        request,
        "community/create_group.html",
        {
            "form": form,
        },
    )

# ============================================================
# 5. PROJECT GROUP LISTING
# ============================================================
# Purpose:
# Display public groups and private groups the developer
# already belongs to.
#
# Also determine whether the logged-in developer has joined
# each group, so the correct button can be displayed.
# ============================================================

@login_required
def groups(request):
    """Display project groups available to the logged-in developer."""

    # Find the IDs of groups the developer already belongs to.
    member_group_ids = set(
        GroupMember.objects
        .filter(user=request.user)
        .values_list("group_id", flat=True)
    )

    # Retrieve public groups and private groups the user belongs to.
    project_groups = (
        ProjectGroup.objects
        .filter(
            Q(is_private=False) |
            Q(id__in=member_group_ids)
        )
        .select_related("owner")
        .distinct()
    )

    # Mark each group as joined or not joined.
    for group in project_groups:

        # True means the developer is already a group member.
        # False means the developer has not joined.
        group.is_member = group.id in member_group_ids

    # Display the Project Groups page.
    return render(
        request,
        "community/groups.html",
        {
            "groups": project_groups,
        },
    )

# ============================================================
# 6. JOIN PUBLIC PROJECT GROUP
# ============================================================
# Purpose:
# Allow logged-in developers to join public groups.
#
# Rules:
# - Public groups can be joined directly.
# - Private groups cannot be joined without authorization.
# - A developer cannot join the same group twice.
# ============================================================

@login_required
@require_POST
def join_group(request, group_id):
    """Allow a logged-in developer to join a public project group."""

    # Find the group or return a 404 error.
    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
        is_private=False,
    )

    # Add the developer only if they are not already a member.
    GroupMember.objects.get_or_create(
        group=group,
        user=request.user,
        defaults={
            "role": "member",
        },
    )

    # Redirect to the group listing for now.
    return redirect("groups")

    # ============================================================
# 7. PROJECT GROUP DETAILS
# ============================================================
# Purpose:
# Display the inside of a project group.
#
# Rules:
# - Only group members can enter.
# - The group description is visible inside the group.
# - Nonmembers cannot access the group by typing its URL.
# ============================================================

@login_required
def group_detail(request, group_id):
    """Display a project group to its members."""

    # Find the group or return a 404 error.
    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
    )

    # Check whether the developer belongs to this group.
    is_member = GroupMember.objects.filter(
        group=group,
        user=request.user,
    ).exists()

    # Block developers who are not group members.
    if not is_member:
        return redirect("groups")

    # Retrieve group members and their roles.
    members = (
        GroupMember.objects
        .filter(group=group)
        .select_related("user")
        .order_by("joined_at")
    )

    # Display the group's private workspace.
    return render(
        request,
        "community/group_detail.html",
        {
            "group": group,
            "members": members,
        },
    )