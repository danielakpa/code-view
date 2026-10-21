"""Forms for creating community posts."""

from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    """Collect and validate information for a new post."""

    class Meta:
        # Connect this form to our Post database model.
        model = Post

        # These are the fields users can fill in.
        fields = ["title", "content"]

        # Customize how the fields appear in HTML.
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Enter your post title",
                    "class": "post-input",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "placeholder": "Ask a question or share your code...",
                    "class": "post-textarea",
                    "rows": 5,
                }
            ),
        }