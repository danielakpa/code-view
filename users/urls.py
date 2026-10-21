from django.urls import path
from .views import register, user_login

urlpatterns = [
    # New users create an account.
    path("register/", register, name="register"),

    # Existing users log in.
    path("login/", user_login, name="login"),
]