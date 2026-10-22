"""Handle project groups and their members."""

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProjectGroupForm
from .models import GroupMember, ProjectGroup


# ============================================================
# 1. GROUPS DASHBOARD
# ============================================================

@login_required
def groups(request):
    """Show public groups and private groups the user belongs to."""

    # Find groups the logged-in developer has joined.
    member_group_ids = set(
        GroupMember.objects
        .filter(user=request.user)
        .values_list("group_id", flat=True)
    )

    # Show public groups and private groups the user belongs to.
    project_groups = (
        ProjectGroup.objects
        .filter(
            Q(is_private=False) |
            Q(id__in=member_group_ids)
        )
        .select_related("owner")
        .distinct()
    )

    # Tell the template whether the developer belongs to each group.
    for group in project_groups:
        group.is_member = group.id in member_group_ids

    return render(
        request,
        "community/groups.html",
        {"groups": project_groups},
    )


# ============================================================
# 2. CREATE GROUP
# ============================================================

@login_required
def create_group(request):
    """Create a group and make its creator an admin."""

    if request.method == "POST":
        form = ProjectGroupForm(request.POST)

        if form.is_valid():

            # Both database operations must succeed together.
            with transaction.atomic():

                group = form.save(commit=False)
                group.owner = request.user
                group.save()

                # Automatically add the creator as group admin.
                GroupMember.objects.create(
                    group=group,
                    user=request.user,
                    role="admin",
                )

            return redirect("groups")

    else:
        form = ProjectGroupForm()

    return render(
        request,
        "community/create_group.html",
        {"form": form},
    )


# ============================================================
# 3. JOIN PUBLIC GROUP
# ============================================================

@login_required
@require_POST
def join_group(request, group_id):
    """Allow a developer to join a public group."""

    # Private groups cannot be joined through this endpoint.
    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
        is_private=False,
    )

    # Prevent duplicate group memberships.
    GroupMember.objects.get_or_create(
        group=group,
        user=request.user,
        defaults={"role": "member"},
    )

    return redirect("groups")


# ============================================================
# 4. GROUP DETAILS
# ============================================================

@login_required
def group_detail(request, group_id):
    """Allow members to enter their group workspace."""

    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
    )

    # Check whether this developer belongs to the group.
    is_member = GroupMember.objects.filter(
        group=group,
        user=request.user,
    ).exists()

    # Nonmembers cannot enter the group workspace.
    if not is_member:
        return redirect("groups")

    # Retrieve group members and their roles.
    members = (
        GroupMember.objects
        .filter(group=group)
        .select_related("user")
        .order_by("joined_at")
    )

    return render(
        request,
        "community/group_detail.html",
        {
            "group": group,
            "members": members,
        },
    )