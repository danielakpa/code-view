"""Forms for project groups and group discussions."""

from django import forms

from .models import (
    ProjectGroup,
    GroupDiscussion,
    GroupDiscussionComment,
)


# ============================================================
# 1. CREATE PROJECT GROUP
# ============================================================

class ProjectGroupForm(forms.ModelForm):
    """Collect information for a new project group."""

    class Meta:
        model = ProjectGroup

        fields = [
            "name",
            "description",
            "is_private",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter your project group name",
                    "class": "group-input",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "placeholder": "What will your group work on?",
                    "class": "group-textarea",
                    "rows": 4,
                }
            ),

            "is_private": forms.CheckboxInput(
                attrs={
                    "class": "group-checkbox",
                }
            ),
        }

    def clean_name(self):
        """Remove spaces and reject empty group names."""

        name = self.cleaned_data["name"].strip()

        if not name:
            raise forms.ValidationError(
                "Please enter a group name."
            )

        return name


# ============================================================
# 2. GROUP DISCUSSION
# ============================================================

class GroupDiscussionForm(forms.ModelForm):
    """Collect the title and content of a group discussion."""

    class Meta:
        model = GroupDiscussion

        fields = [
            "title",
            "content",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Enter discussion title",
                    "class": "group-input",
                }
            ),

            "content": forms.Textarea(
                attrs={
                    "placeholder": "What would you like to discuss?",
                    "class": "group-textarea",
                    "rows": 5,
                }
            ),
        }

    def clean_title(self):
        """Reject empty discussion titles."""

        title = self.cleaned_data["title"].strip()

        if not title:
            raise forms.ValidationError(
                "Please enter a discussion title."
            )

        return title

    def clean_content(self):
        """Reject empty discussion messages."""

        content = self.cleaned_data["content"].strip()

        if not content:
            raise forms.ValidationError(
                "Please enter a discussion message."
            )

        return content


# ============================================================
# 3. GROUP DISCUSSION COMMENT
# ============================================================

class GroupDiscussionCommentForm(forms.ModelForm):
    """Collect comments underneath group discussions."""

    class Meta:
        model = GroupDiscussionComment

        fields = ["content"]

        widgets = {
            "content": forms.Textarea(
                attrs={
                    "placeholder": "Write your comment...",
                    "class": "group-textarea",
                    "rows": 3,
                }
            ),
        }

    def clean_content(self):
        """Reject empty group discussion comments."""

        content = self.cleaned_data["content"].strip()

        if not content:
            raise forms.ValidationError(
                "Please enter a comment."
            )

        return content