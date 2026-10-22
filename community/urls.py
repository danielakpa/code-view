"""URL routes for CodeView project groups."""

from django.urls import path
from . import views


urlpatterns = [

    # Main Groups Dashboard.
    path(
        "",
        views.groups,
        name="groups",
    ),

    # Create a new group.
    path(
        "create/",
        views.create_group,
        name="create_group",
    ),

    # Join an existing public group.
    path(
        "<int:group_id>/join/",
        views.join_group,
        name="join_group",
    ),

    # Enter a group workspace.
    path(
        "<int:group_id>/",
        views.group_detail,
        name="group_detail",
    ),

]