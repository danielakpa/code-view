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

    # Display available project groups.
    path(
        "groups/",
        views.groups,
        name="groups",
    ),

# Create a new project group.
    path(
        "groups/create/",
        views.create_group,
        name="create_group",
    ),

    # Join a public project group.
    path(
        "groups/<int:group_id>/join/",
        views.join_group,
        name="join_group",
    ),
        # ========================================================
    # PROJECT GROUP DETAILS
    # ========================================================

    path(
        "groups/<int:group_id>/",
        views.group_detail,
        name="group_detail",
    ),
]