"""Handle the CodeView community dashboard and posts."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import PostForm
from .models import Post


@login_required
def community(request):
    """Display community posts and allow logged-in users to create posts."""

    # Check whether the user submitted the post form.
    if request.method == "POST":

        # Collect the submitted information.
        form = PostForm(request.POST)

        # Check that the title and content are valid.
        if form.is_valid():

            # Create the post object without saving it yet.
            post = form.save(commit=False)

            # Connect the post to the logged-in user.
            post.author = request.user

            # Save the post to PostgreSQL.
            post.save()

            # Redirect to prevent duplicate posts on page refresh.
            return redirect("community")

    else:
        # Display an empty form when the page first opens.
        form = PostForm()

    # Retrieve posts from PostgreSQL, newest first.
    posts = Post.objects.select_related("author").all()

    # Send the form and posts to the HTML template.
    return render(
        request,
        "community/community.html",
        {
            "form": form,
            "posts": posts,
        },
    )