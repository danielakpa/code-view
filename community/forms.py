"""Forms for community posts and comments."""

from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Validate new community posts."""

    class Meta:
        model = Post

        # Community posts have content but no title.
        fields = ["content"]

        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "post-textarea",
                    "placeholder": "Ask a question or share your code...",
                    "rows": 5,
                    "required": True,
                }
            ),
        }

    def clean_content(self):
        """Reject posts containing only spaces."""

        content = self.cleaned_data["content"].strip()

        if not content:
            raise forms.ValidationError(
                "Please write something before publishing."
            )

        return content


class CommentForm(forms.ModelForm):
    """Validate comments submitted underneath posts."""

    class Meta:
        model = Comment

        fields = ["content"]

        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "comment-textarea",
                    "placeholder": "Write a comment...",
                    "rows": 2,
                    "maxlength": 2000,
                    "required": True,
                }
            ),
        }

    def clean_content(self):
        """Reject empty comments."""

        content = self.cleaned_data["content"].strip()

        if not content:
            raise forms.ValidationError(
                "Please write a comment."
            )

        return content