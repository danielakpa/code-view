"""Forms for CodeView community posts, comments, and project groups."""

from django import forms

from .models import Post, Comment, ProjectGroup


# ============================================================
# 1. COMMUNITY POST FORM
# ============================================================
# Purpose:
# Allow developers to create posts in the public community.
# Posts can contain questions, explanations, or code snippets.
# Community posts do not require titles.
# ============================================================

class PostForm(forms.ModelForm):
    """Collect and validate new community posts."""

    class Meta:
        # Connect this form to the Post database model.
        model = Post

        # Only allow developers to submit post content.
        fields = ["content"]

        # Customize how the content input appears in HTML.
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
        """Prevent developers from publishing empty posts."""

        # Get the submitted content and remove surrounding spaces.
        content = self.cleaned_data["content"].strip()

        # Reject content containing only spaces.
        if not content:
            raise forms.ValidationError(
                "Please write something before publishing."
            )

        # Return the validated content.
        return content


# ============================================================
# 2. COMMUNITY COMMENT FORM
# ============================================================
# Purpose:
# Allow developers to comment underneath community posts.
# Comments help developers ask questions, provide answers,
# and discuss programming ideas.
# ============================================================

class CommentForm(forms.ModelForm):
    """Collect and validate comments underneath posts."""

    class Meta:
        # Connect this form to the Comment database model.
        model = Comment

        # Developers can submit only the comment message.
        fields = ["content"]

        # Customize the comment input field.
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
        """Prevent developers from submitting empty comments."""

        # Get the submitted comment and remove surrounding spaces.
        content = self.cleaned_data["content"].strip()

        # Reject comments containing only spaces.
        if not content:
            raise forms.ValidationError(
                "Please write a comment."
            )

        # Return the validated comment.
        return content


# ============================================================
# 3. PROJECT GROUP FORM
# ============================================================
# Purpose:
# Allow developers to create collaboration groups.
# Each group has a name, description, and privacy setting.
#
# Public group:
# Other developers can discover the group.
#
# Private group:
# Only authorized members can access the group.
#
# The group owner is assigned in views.py, not this form.
# ============================================================

class ProjectGroupForm(forms.ModelForm):
    """Collect and validate new project group information."""

    class Meta:
        # Connect this form to the ProjectGroup database model.
        model = ProjectGroup

        # Allow developers to provide these three fields.
        fields = [
            "name",
            "description",
            "is_private",
        ]

        # Customize the HTML inputs.
        widgets = {
            # Input for the project group name.
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter your project group name",
                    "class": "group-input",
                }
            ),

            # Text area for describing the group's purpose.
            "description": forms.Textarea(
                attrs={
                    "placeholder": "What will your group work on?",
                    "class": "group-textarea",
                    "rows": 4,
                }
            ),

            # Checkbox for choosing private or public.
            "is_private": forms.CheckboxInput(
                attrs={
                    "class": "group-checkbox",
                }
            ),
        }

    def clean_name(self):
        """Validate the project group name."""

        # Get the name and remove unnecessary spaces.
        name = self.cleaned_data["name"].strip()

        # Reject an empty name.
        if not name:
            raise forms.ValidationError(
                "Please enter a group name."
            )

        # Return the validated group name.
        return name