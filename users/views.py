from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegisterForm


def register(request):
    # Check whether the user submitted the registration form.
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            # Create the user account in PostgreSQL.
            user = form.save()

            # Automatically log the new user in.
            login(request, user)

            # Redirect directly to the Community page.
            return redirect("community")

    else:
        # Display an empty registration form.
        form = RegisterForm()

    # Show the form again if registration fails.
    return render(request, "users/register.html", {"form": form})