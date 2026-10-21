"""URL routes for the CodeView Community."""

from django.urls import path

from . import views


urlpatterns = [
    # Community homepage.
    path(
        "",
        views.community,
        name="community",
    ),

    # Add a comment underneath a post.
    path(
        "posts/<int:post_id>/comment/",
        views.add_comment,
        name="add_comment",
    ),

    # Like or unlike a post.
    path(
        "posts/<int:post_id>/like/",
        views.toggle_like,
        name="toggle_like",
    ),
]