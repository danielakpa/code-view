"""Forms for CodeView community posts and comments."""

from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Collect and validate community posts."""

    class Meta:
        model = Post

        # Community posts don't need titles.
        fields = ["content"]

        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "post-textarea",
                    "placeholder": "Ask a question or share your code...",
                    "rows": 5,
                }
            ),
        }


class CommentForm(forms.ModelForm):
    """Collect and validate comments under posts."""

    class Meta:
        model = Comment

        fields = ["content"]

        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "comment-textarea",
                    "placeholder": "Write a comment...",
                    "rows": 2,
                }
            ),
        }