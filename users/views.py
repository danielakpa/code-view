from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth import login


def register(request):
    # Check if the user submitted the registration form.
    if request.method == "POST":

        # Collect and validate the submitted information.
        form = RegisterForm(request.POST)

      if form.is_valid():
    # Create the new user.
    user = form.save()

    # Automatically log the user in.
    login(request, user)

    # Send the user to the community.
    return redirect("community")

    else:
        # Display an empty form when the page first opens.
        form = RegisterForm()

    # Display the registration page and its form.
    return render(request, "users/register.html", {"form": form})



