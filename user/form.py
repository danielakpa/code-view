from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    # Make email compulsory.
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean_email(self):
        # Get the email and remove extra spaces.
        email = self.cleaned_data["email"].strip().lower()

        # Check if another account already uses this email.
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "This email is already registered. Please log in."
            )

        # Return the validated email.
        return email