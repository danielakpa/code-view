"""URL routes for the CodeView Community."""

from django.urls import path
from . import views

urlpatterns = [
    # Main community dashboard.
    path("", views.community, name="community"),

    # Add a comment to a particular post.
    path(
        "posts/<int:post_id>/comment/",
        views.add_comment,
        name="add_comment",
    ),

    # Like or unlike a particular post.
    path(
        "posts/<int:post_id>/like/",
        views.toggle_like,
        name="toggle_like",
    ),
]