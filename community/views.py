"""Handle community posts, comments, and likes."""

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .forms import PostForm, CommentForm
from .models import Post, Comment, Like


@login_required
def community(request):
    """Display community posts and create new posts."""

    if request.method == "POST":
        form = PostForm(request.POST)

        if form.is_valid():
            # Prepare the post without saving immediately.
            post = form.save(commit=False)

            # Set the logged-in user as the author.
            post.author = request.user

            # Save the post to PostgreSQL.
            post.save()

            return redirect("community")
    else:
        form = PostForm()

    # Fetch posts and their authors efficiently.
    posts = (
        Post.objects.select_related("author")
        .prefetch_related("comments__author")
        .annotate(
            likes_count=Count("likes", distinct=True),
            comments_count=Count("comments", distinct=True),
        )
    )

    return render(
        request,
        "community/community.html",
        {
            "form": form,
            "comment_form": CommentForm(),
            "posts": posts,
        },
    )


@login_required
@require_POST
def add_comment(request, post_id):
    """Save a comment underneath a community post."""

    # Make sure the post exists.
    post = get_object_or_404(Post, id=post_id)

    # Validate the submitted comment.
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()

    return redirect("community")


@login_required
@require_POST
def toggle_like(request, post_id):
    """Like or unlike a community post."""

    post = get_object_or_404(Post, id=post_id)

    # Check whether the user has already liked the post.
    like, created = Like.objects.get_or_create(
        post=post,
        user=request.user,
    )

    # Clicking Like again removes the existing like.
    if not created:
        like.delete()

    return redirect("community")