"""Handle community posts, likes, and comments."""

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from .forms import CommentForm, PostForm
from .models import Like, Post


@login_required
def community(request):
    """Display posts and allow developers to publish new ones."""

    # Handle a new post submission.
    if request.method == "POST":
        form = PostForm(request.POST)

        if form.is_valid():
            # Prepare the post without saving immediately.
            post = form.save(commit=False)

            # Set the logged-in developer as the author.
            post.author = request.user

            # Save the post in PostgreSQL.
            post.save()

            # Redirect to prevent duplicate posts on refresh.
            return redirect("community")

    else:
        # Display an empty form for new posts.
        form = PostForm()

    # Fetch posts with their authors and comments.
    posts = (
        Post.objects
        .select_related("author")
        .prefetch_related("comments__author")
        .annotate(
            likes_count=Count("likes", distinct=True),
            comments_count=Count("comments", distinct=True),
        )
    )

    # Find all posts liked by the logged-in developer.
    liked_post_ids = set(
        Like.objects
        .filter(user=request.user)
        .values_list("post_id", flat=True)
    )

    # Mark each post as liked or not liked.
    for post in posts:
        post.is_liked = post.id in liked_post_ids

    # Display the community page.
    return render(
        request,
        "community/community.html",
        {
            "form": form,
            "posts": posts,
            "comment_form": CommentForm(),
        },
    )


@login_required
@require_POST
def add_comment(request, post_id):
    """Add a comment to an existing post."""

    # Find the post or return a 404 error.
    post = get_object_or_404(Post, id=post_id)

    # Validate the submitted comment.
    form = CommentForm(request.POST)

    if form.is_valid():
        # Prepare the comment.
        comment = form.save(commit=False)

        # Connect the comment to the post and developer.
        comment.post = post
        comment.author = request.user

        # Save the comment in PostgreSQL.
        comment.save()

    # Return to the post and open its comments.
    return redirect(f"/community/?comments={post.id}#post-{post.id}")


@login_required
@require_POST
def toggle_like(request, post_id):
    """Like or unlike a community post."""

    # Find the post.
    post = get_object_or_404(Post, id=post_id)

    # Create a like if the developer has not liked the post.
    like, created = Like.objects.get_or_create(
        post=post,
        user=request.user,
    )

    # If a like already exists, remove it.
    if not created:
        like.delete()

    # Return to the same post.
    return redirect(f"/community/#post-{post.id}")