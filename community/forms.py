
"""Forms for CodeView Community."""

from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    """Validate content submitted to the community feed."""

    class Meta:
        model = Post

        # Community posts do not need a title.
        fields = ["content"]

        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "post-textarea",
                    "placeholder": (
                        "Ask a question, share an idea, "
                        "or paste your code here..."
                    ),
                    "rows": 6,
                }
            ),
        }
