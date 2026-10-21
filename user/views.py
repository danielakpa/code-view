from django.shortcuts import render, redirect
from .forms import RegisterForm


def register(request):
    # Check if the user submitted the registration form.
    if request.method == "POST":

        # Collect and validate the submitted information.
        form = RegisterForm(request.POST)

        if form.is_valid():
            # Save the new user to PostgreSQL.
            form.save()

            # Redirect the user to the homepage.
            return redirect("home_page")

    else:
        # Display an empty form when the page first opens.
        form = RegisterForm()

    # Display the registration page and its form.
    return render(request, "users/register.html", {"form": form})