from django.urls import path
from .views import register

# URLs belonging to the users app.
urlpatterns = [
    path("register/", register, name="register"),
]