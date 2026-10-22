"""Main URL configuration for CodeView."""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from home.views import home


# Django looks for this exact variable name: urlpatterns
urlpatterns = [

    # Django admin panel.
    path("admin/", admin.site.urls),

    # Homepage.
    path("", home, name="home"),

    # Registration and login.
    path("", include("users.urls")),

    # Project Groups.
    path("groups/", include("community.urls")),

    # Redirect old Community URLs to Groups.
    path(
        "community/",
        RedirectView.as_view(
            pattern_name="groups",
            permanent=False,
        ),
    ),

]