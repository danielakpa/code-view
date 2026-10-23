"""Handle CodeView groups, memberships, discussions, chat, and workspaces."""
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.urls import reverse
from django.shortcuts import redirect
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Q, Count
from django.http import (
    HttpResponseForbidden,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    ProjectGroupForm,
    GroupDiscussionForm,
    GroupDiscussionCommentForm,
    GroupChatMessageForm,
)

from .models import (
    ProjectGroup,
    GroupMember,
    GroupMembershipRequest,
    GroupDiscussion,
    GroupDiscussionComment,
    GroupDiscussionLike,
    HiddenDiscussion,
    GroupChatMessage,
    GroupCodeBoard,
)


# ============================================================
# HELPER: CHECK GROUP MEMBERSHIP
# ============================================================

def is_group_member(group, user):
    """Return True when the developer belongs to the group."""

    return GroupMember.objects.filter(
        group=group,
        user=user,
    ).exists()


# ============================================================
# 1. GROUPS DASHBOARD
# ============================================================

@login_required
def groups(request):
    """Display discoverable communities and the user's private groups."""

    member_group_ids = set(
        GroupMember.objects
        .filter(user=request.user)
        .values_list("group_id", flat=True)
    )

    pending_group_ids = set(
        GroupMembershipRequest.objects
        .filter(
            user=request.user,
            status="pending",
        )
        .values_list("group_id", flat=True)
    )

    # Show public communities and private groups the user belongs to.
    project_groups = (
        ProjectGroup.objects
        .filter(
            Q(is_private=False) |
            Q(id__in=member_group_ids)
        )
        .select_related("owner")
        .distinct()
    )

    for group in project_groups:

        group.is_member = group.id in member_group_ids

        group.has_pending_request = (
            group.id in pending_group_ids
        )

    return render(
        request,
        "community/groups.html",
        {
            "groups": project_groups,
        },
    )


# ============================================================
# 2. CREATE GROUP
# ============================================================

@login_required
def create_group(request):
    """Create a group and make its creator an administrator."""

    if request.method == "POST":

        form = ProjectGroupForm(request.POST)

        if form.is_valid():

            with transaction.atomic():

                group = form.save(commit=False)

                group.owner = request.user

                # Private groups cannot allow unrestricted joining.
                if group.is_private and group.join_policy == "open":
                    group.join_policy = "approval"

                group.save()

                # The group creator becomes the first administrator.
                GroupMember.objects.create(
                    group=group,
                    user=request.user,
                    role="admin",
                )

            messages.success(
                request,
                "Your group was created successfully!",
            )

            return redirect("groups")

    else:
        form = ProjectGroupForm()

    return render(
        request,
        "community/create_group.html",
        {
            "form": form,
        },
    )


# ============================================================
# 3. JOIN OR REQUEST TO JOIN A GROUP
# ============================================================

@login_required
@require_POST
def join_group(request, group_id):
    """Join an open group or submit a membership request."""

    redirect_to_group = False

    with transaction.atomic():

        # Lock the group to coordinate membership changes.
        group = get_object_or_404(
            ProjectGroup.objects.select_for_update(),
            id=group_id,
        )

        already_member = is_group_member(
            group,
            request.user,
        )

        if already_member:

            messages.info(
                request,
                "You are already a member of this group.",
            )

            redirect_to_group = True

        elif group.join_policy == "invite":

            return HttpResponseForbidden(
                "This group requires an invitation."
            )

        elif group.join_policy == "open":

            if group.is_private:

                return HttpResponseForbidden(
                    "Private groups cannot allow open joining."
                )

            GroupMember.objects.get_or_create(
                group=group,
                user=request.user,
                defaults={
                    "role": "member",
                },
            )

            messages.success(
                request,
                "You joined the community successfully!",
            )

            redirect_to_group = True

        elif group.join_policy == "approval":

            existing_request = GroupMembershipRequest.objects.filter(
                group=group,
                user=request.user,
            ).first()

            if (
                existing_request is not None
                and existing_request.status == "pending"
            ):

                messages.info(
                    request,
                    "Your membership request is already pending approval.",
                )

            else:

                introduction = request.POST.get(
                    "message",
                    "",
                ).strip()[:1000]

                if existing_request is not None:

                    existing_request.status = "pending"
                    existing_request.message = introduction
                    existing_request.reviewed_by = None
                    existing_request.reviewed_at = None
                    existing_request.save()

                else:

                    GroupMembershipRequest.objects.create(
                        group=group,
                        user=request.user,
                        message=introduction,
                    )

                messages.success(
                    request,
                    (
                        "Membership request sent successfully! "
                        "Please wait for administrator approval."
                    ),
                )

        else:

            return HttpResponseBadRequest(
                "Invalid group joining policy."
            )

    if redirect_to_group:

        return redirect(
            "group_detail",
            group_id=group_id,
        )

    if not group.is_private:

        return redirect(
            "group_detail",
            group_id=group_id,
        )

    return redirect("groups")


# ============================================================
# 4. GROUP DETAILS
# ============================================================
@login_required
def group_detail(request, group_id):
    """
    Display the unified group workspace.

    The workspace contains:
    1. Discussions
    2. Group Chat
    3. Group Members

    Chat messages are loaded only for group members.
    """

    # Find the group or return 404 if it does not exist.
    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
    )

    # Check whether the logged-in developer belongs to this group.
    membership = GroupMember.objects.filter(
        group=group,
        user=request.user,
    ).first()

    # Only members can enter private groups.
    if group.is_private and membership is None:
        return HttpResponseForbidden(
            "You must be a member to access this private group."
        )

    # Store membership status for easier checking.
    is_member = membership is not None

    # Load the members of this group.
    members = (
        GroupMember.objects
        .filter(group=group)
        .select_related("user")
        .order_by("joined_at")
    )

    # Check whether the developer has a pending membership request.
    pending_request = GroupMembershipRequest.objects.filter(
        group=group,
        user=request.user,
        status="pending",
    ).exists()

    # Check whether the developer is a group administrator.
    is_admin = (
        is_member
        and membership.role == "admin"
    )

    # ========================================
    # 1. LOAD GROUP DISCUSSIONS
    # ========================================

    # Find discussions hidden by the logged-in developer.
    hidden_discussion_ids = HiddenDiscussion.objects.filter(
        user=request.user,
    ).values_list(
        "discussion_id",
        flat=True,
    )

    # Load the latest 20 discussions.
    discussions = list(
        GroupDiscussion.objects
        .filter(group=group)
        .exclude(id__in=hidden_discussion_ids)
        .select_related("author")
        .annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", distinct=True),
        )
        .order_by("-created_at")[:20]
    )

    # Find discussions already liked by this developer.
    liked_discussion_ids = set(
        GroupDiscussionLike.objects
        .filter(
            user=request.user,
            discussion__in=discussions,
        )
        .values_list("discussion_id", flat=True)
    )

    # Mark each discussion as liked or not liked.
    for discussion in discussions:
        discussion.liked_by_user = (
            discussion.id in liked_discussion_ids
        )

    # ========================================
    # 2. LOAD GROUP CHAT
    # ========================================

    # Default values for developers who are not members.
    chat_messages = []
    chat_form = None

    # Only group members can access chat information.
    if is_member:

        # Fetch the latest 50 messages.
        chat_messages = list(
            GroupChatMessage.objects
            .filter(group=group)
            .select_related(
                "sender",
                "reply_to",
                "reply_to__sender",
            )
            .order_by("-created_at", "-id")[:50]
        )

        # Display messages from oldest to newest.
        chat_messages.reverse()

        # Create the form used to send chat messages.
        chat_form = GroupChatMessageForm()

    # ========================================
    # 3. RENDER THE UNIFIED WORKSPACE
    # ========================================

    return render(
        request,
        "community/group_detail.html",
        {
            # Group information.
            "group": group,

            # Membership information.
            "members": members,
            "is_member": is_member,
            "is_admin": is_admin,
            "pending_request": pending_request,

            # Discussion information.
            "discussions": discussions,

            # Chat information.
            "chat_messages": chat_messages,
            "chat_form": chat_form,
        },
    )

# ============================================================
# 5. REVIEW MEMBERSHIP REQUESTS
# ============================================================

@login_required
def membership_requests(request, group_id):
    """Show pending membership requests to administrators."""

    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
    )

    is_admin = GroupMember.objects.filter(
        group=group,
        user=request.user,
        role="admin",
    ).exists()

    if not is_admin:

        return HttpResponseForbidden(
            "Only group administrators can review membership requests."
        )

    pending_requests = (
        GroupMembershipRequest.objects
        .filter(
            group=group,
            status="pending",
        )
        .select_related("user")
        .order_by("created_at")
    )

    return render(
        request,
        "community/membership_requests.html",
        {
            "group": group,
            "pending_requests": pending_requests,
        },
    )


# ============================================================
# 6. APPROVE MEMBERSHIP REQUEST
# ============================================================

@login_required
@require_POST
def approve_membership(request, group_id, request_id):
    """Approve a membership request without exceeding group limits."""

    with transaction.atomic():

        group = get_object_or_404(
            ProjectGroup.objects.select_for_update(),
            id=group_id,
        )

        is_admin = GroupMember.objects.filter(
            group=group,
            user=request.user,
            role="admin",
        ).exists()

        if not is_admin:

            return HttpResponseForbidden(
                "Only group administrators can approve members."
            )

        membership_request = get_object_or_404(
            GroupMembershipRequest.objects.select_for_update(),
            id=request_id,
            group=group,
        )

        if membership_request.status != "pending":

            return HttpResponseBadRequest(
                "This request has already been reviewed."
            )

        already_member = GroupMember.objects.filter(
            group=group,
            user=membership_request.user,
        ).exists()

        if already_member:

            return HttpResponseBadRequest(
                "This developer is already a group member."
            )

        if group.is_private:

            member_count = GroupMember.objects.filter(
                group=group,
            ).count()

            if member_count >= 10:

                messages.error(
                    request,
                    "This private development group already has 10 members.",
                )

                return redirect(
                    "membership_requests",
                    group_id=group.id,
                )

        # Approve the request BEFORE creating the membership.
        #
        # This avoids the membership request model rejecting
        # the update because the developer is already a member.
        membership_request.status = "approved"
        membership_request.reviewed_by = request.user
        membership_request.reviewed_at = timezone.now()
        membership_request.save()

        GroupMember.objects.create(
            group=group,
            user=membership_request.user,
            role="member",
        )

        messages.success(
            request,
            (
                f"{membership_request.user.username} "
                "was approved successfully!"
            ),
        )

    return redirect(
        "membership_requests",
        group_id=group_id,
    )


# ============================================================
# 7. REJECT MEMBERSHIP REQUEST
# ============================================================

@login_required
@require_POST
def reject_membership(request, group_id, request_id):
    """Reject a pending membership request."""

    with transaction.atomic():

        group = get_object_or_404(
            ProjectGroup.objects.select_for_update(),
            id=group_id,
        )

        is_admin = GroupMember.objects.filter(
            group=group,
            user=request.user,
            role="admin",
        ).exists()

        if not is_admin:

            return HttpResponseForbidden(
                "Only group administrators can reject requests."
            )

        membership_request = get_object_or_404(
            GroupMembershipRequest.objects.select_for_update(),
            id=request_id,
            group=group,
        )

        if membership_request.status != "pending":

            return HttpResponseBadRequest(
                "This request has already been reviewed."
            )

        membership_request.status = "rejected"
        membership_request.reviewed_by = request.user
        membership_request.reviewed_at = timezone.now()
        membership_request.save()

        messages.success(
            request,
            (
                f"Membership request from "
                f"{membership_request.user.username} was rejected."
            ),
        )

    return redirect(
        "membership_requests",
        group_id=group_id,
    )


# ============================================================
# 8. PRIVATE GROUP MEETING ROOM
# ============================================================

@login_required
def meeting_room(request, group_id):
    """Allow private development group members into their meeting room."""

    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
    )

    if not group.is_private:

        return HttpResponseForbidden(
            "Meeting rooms are only available to private development groups."
        )

    if not is_group_member(group, request.user):

        return HttpResponseForbidden(
            "You must belong to this group to enter its meeting room."
        )

    return render(
        request,
        "community/meeting_room.html",
        {
            "group": group,
        },
    )


# ============================================================
# 9. PRIVATE GROUP CODE BOARD
# ============================================================

@login_required
def code_board(request, group_id):
    """Display and save a private development group's code board."""

    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
    )

    if not group.is_private:

        return HttpResponseForbidden(
            "Code boards are only available to private development groups."
        )

    if not is_group_member(group, request.user):

        return HttpResponseForbidden(
            "You must belong to this group to access its code board."
        )

    board, created = GroupCodeBoard.objects.get_or_create(
        group=group,
    )

    if request.method == "POST":

        title = request.POST.get("title", "").strip()
        language = request.POST.get("language", "python")
        code = request.POST.get("code", "")

        valid_languages = [
            choice[0]
            for choice in GroupCodeBoard.LANGUAGE_CHOICES
        ]

        if language not in valid_languages:

            return HttpResponseBadRequest(
                "Invalid programming language."
            )

        board.title = title or "Untitled Code"
        board.language = language
        board.code = code
        board.last_edited_by = request.user
        board.save()

        return redirect(
            "code_board",
            group_id=group.id,
        )

    return render(
        request,
        "community/code_board.html",
        {
            "group": group,
            "board": board,
        },
    )


# ============================================================
# 10. CREATE GROUP DISCUSSION
# ============================================================

@login_required
@require_POST
def create_discussion(request, group_id):
    """Allow group members to create discussion posts."""

    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
    )

    # Only members can create discussion posts.
    if not is_group_member(group, request.user):

        return HttpResponseForbidden(
            "You must be a group member to create discussions."
        )

    form = GroupDiscussionForm(request.POST)

    if form.is_valid():

        discussion = form.save(commit=False)

        # Never trust the browser to choose the author or group.
        discussion.group = group
        discussion.author = request.user
        discussion.save()

        messages.success(
            request,
            "Your discussion was posted successfully!",
        )

        return redirect(
            "group_detail",
            group_id=group.id,
        )

    messages.error(
        request,
        "Please enter a valid discussion title and message.",
    )

    return redirect(
        "group_detail",
        group_id=group.id,
    )


# ============================================================
# 11. DISCUSSION DETAILS AND COMMENTS
# ============================================================

@login_required
def discussion_detail(request, group_id, discussion_id):
    """Display a discussion and its comments and replies."""

    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
    )

    # Public communities are discoverable, but only members
    # can participate. Private discussions require membership.
    if group.is_private and not is_group_member(group, request.user):

        return HttpResponseForbidden(
            "You must be a member to view this discussion."
        )

    discussion = get_object_or_404(
        GroupDiscussion.objects.select_related("author"),
        id=discussion_id,
        group=group,
    )

    # A hidden discussion should remain hidden from its user.
    is_hidden = HiddenDiscussion.objects.filter(
        discussion=discussion,
        user=request.user,
    ).exists()

    if is_hidden:

        return HttpResponseForbidden(
            "You have hidden this discussion."
        )

    # Load all comments and replies for the discussion.
    #
    # The template will use each comment's parent_id
    # to display nested conversations.
    comments = (
        GroupDiscussionComment.objects
        .filter(discussion=discussion)
        .select_related("author", "parent")
        .order_by("created_at", "id")
    )

    liked_by_user = GroupDiscussionLike.objects.filter(
        discussion=discussion,
        user=request.user,
    ).exists()

    return render(
        request,
        "community/discussion_detail.html",
        {
            "group": group,
            "discussion": discussion,
            "comments": comments,
            "liked_by_user": liked_by_user,
            "is_member": is_group_member(group, request.user),
            "comment_form": GroupDiscussionCommentForm(),
        },
    )


# ============================================================
# 12. ADD COMMENT OR REPLY
# ============================================================

@login_required
@require_POST
def add_discussion_comment(request, group_id, discussion_id):
    """Allow members to comment or reply to another comment."""

    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
    )

    if not is_group_member(group, request.user):

        return HttpResponseForbidden(
            "You must be a group member to comment."
        )

    discussion = get_object_or_404(
        GroupDiscussion,
        id=discussion_id,
        group=group,
    )

    form = GroupDiscussionCommentForm(request.POST)

    if not form.is_valid():

        messages.error(
            request,
            "Please enter a valid comment.",
        )

        return redirect(
            "discussion_detail",
            group_id=group.id,
            discussion_id=discussion.id,
        )

    comment = form.save(commit=False)

    comment.discussion = discussion
    comment.author = request.user

    # Optional parent comment ID.
    #
    # Empty means a normal comment.
    # A valid ID means a reply to another comment.
    parent_id = request.POST.get("parent_id", "").strip()

    if parent_id:

        parent_comment = get_object_or_404(
            GroupDiscussionComment,
            id=parent_id,
            discussion=discussion,
        )

        comment.parent = parent_comment

        # Save the developer's comment in PostgreSQL.
    comment.save()

    # Return to the discussion without displaying
    # a success notification.
    return redirect(
        "discussion_detail",
        group_id=group.id,
        discussion_id=discussion.id,
    )

# ============================================================
# 13. LIKE OR UNLIKE DISCUSSION
# ============================================================
@login_required
@require_POST
def toggle_discussion_like(request, group_id, discussion_id):
    """Like or unlike a discussion without refreshing the page."""

    # 1. Find the group.
    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
    )

    # 2. Check whether the developer belongs to the group.
    if not is_group_member(group, request.user):
        return HttpResponseForbidden(
            "You must be a group member to like discussions."
        )

    # 3. Find the discussion.
    discussion = get_object_or_404(
        GroupDiscussion,
        id=discussion_id,
        group=group,
    )

    # 4. Save or remove the like.
    with transaction.atomic():

        # Get the actual Django User model.
        User = get_user_model()

        # Lock the user's database record.
        # This prevents overlapping Like requests
        # from the same developer.
        User.objects.select_for_update().get(
            pk=request.user.pk
        )

        # Check whether the developer already liked this post.
        existing_like = GroupDiscussionLike.objects.filter(
            discussion=discussion,
            user=request.user,
        ).first()

        if existing_like:

            # Remove the existing like.
            existing_like.delete()
            liked = False

        else:

            # Save a new like.
            GroupDiscussionLike.objects.create(
                discussion=discussion,
                user=request.user,
            )
            liked = True

        # Count the total likes after the change.
        like_count = GroupDiscussionLike.objects.filter(
            discussion=discussion,
        ).count()

    # 5. Return JSON when JavaScript sends the request.
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        return JsonResponse({
            "liked": liked,
            "like_count": like_count,
        })

    # 6. If JavaScript is not used, return to the discussion.
    return redirect(
        "discussion_detail",
        group_id=group.id,
        discussion_id=discussion.id,
    )
# ============================================================
# 14. HIDE DISCUSSION
# ============================================================

@login_required
@require_POST
def hide_discussion(request, group_id, discussion_id):
    """Hide a discussion only for the current developer."""

    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
    )

    if not is_group_member(group, request.user):

        return HttpResponseForbidden(
            "You must be a group member to hide discussions."
        )

    discussion = get_object_or_404(
        GroupDiscussion,
        id=discussion_id,
        group=group,
    )

    HiddenDiscussion.objects.get_or_create(
        discussion=discussion,
        user=request.user,
    )

    messages.success(
        request,
        "Discussion hidden from your feed.",
    )

    return redirect(
        "group_detail",
        group_id=group.id,
    )


# ============================================================
# 15. GROUP CHAT ROOM
# ============================================================

@login_required
def group_chat(request, group_id):
    """Display chat history to authorized group members."""

    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
    )

    # Both public and private chats require group membership.
    if not is_group_member(group, request.user):

        return HttpResponseForbidden(
            "You must be a group member to access its chat."
        )

    # Load the latest 50 messages.
    #
    # Fetch newest messages first for efficiency,
    # then reverse them for chronological display.
    recent_messages = list(
        GroupChatMessage.objects
        .filter(group=group)
        .select_related("sender", "reply_to")
        .order_by("-created_at", "-id")[:50]
    )

    recent_messages.reverse()

    return render(
        request,
        "community/group_chat.html",
        {
            "group": group,
            "chat_messages": recent_messages,
            "chat_form": GroupChatMessageForm(),
        },
    )


# ============================================================
# 16. SEND GROUP CHAT MESSAGE
# ============================================================
@login_required
@require_POST
def send_group_message(request, group_id):
    """Save a group message and broadcast it through WebSockets."""

    # Find the group or return 404.
    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
    )

    # Only group members can send messages.
    if not is_group_member(group, request.user):
        return HttpResponseForbidden(
            "You must be a group member to send messages."
        )

    # Validate the message and uploaded files.
    form = GroupChatMessageForm(
        request.POST,
        request.FILES,
    )

        # ========================================
    # CHECK IF REQUEST COMES FROM JAVASCRIPT
    # ========================================

    # AJAX requests should receive JSON instead of redirects.
    is_ajax = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )

    # ========================================
    # HANDLE INVALID MESSAGES
    # ========================================

    if not form.is_valid():

        # Return an error response to JavaScript.
        if is_ajax:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Your message is invalid.",
                    "details": form.errors.get_json_data(),
                },
                status=400,
            )

        # Keep the original behavior for normal HTML forms.
        messages.error(
            request,
            "Your message is invalid. Check the content or attachment.",
        )

        return redirect(
            reverse(
                "group_detail",
                kwargs={"group_id": group.id},
            ) + "#group-chat"
        )

    # ========================================
    # CREATE MESSAGE
    # ========================================

    # Create the message without saving immediately.
    chat_message = form.save(commit=False)

    # Assign the group and sender.
    chat_message.group = group
    chat_message.sender = request.user

    # ========================================
    # HANDLE MESSAGE REPLIES
    # ========================================

    reply_to_id = request.POST.get(
        "reply_to_id",
        "",
    ).strip()

    if reply_to_id:

        # Make sure the original message belongs to this group.
        reply_to_message = get_object_or_404(
            GroupChatMessage,
            id=reply_to_id,
            group=group,
        )

        chat_message.reply_to = reply_to_message

    # ========================================
    # SAVE MESSAGE
    # ========================================

    # Save the completed message to the database.
    chat_message.save()

    # ========================================
    # BROADCAST MESSAGE THROUGH WEBSOCKETS
    # ========================================

    # Get Django Channels' communication layer.
    channel_layer = get_channel_layer()

    # This must match the group name in consumers.py.
    room_group_name = f"group_chat_{group.id}"

    # Prepare the data that connected browsers will receive.
    message_data = {
        "type": "message_created",
        "message_id": chat_message.id,
        "group_id": group.id,
        "sender_id": request.user.id,
        "sender": request.user.username,
        "content": chat_message.content,
        "message_type": chat_message.message_type,
        "created_at": chat_message.created_at.isoformat(),
        "reply_to_id": chat_message.reply_to_id,
        "attachment_url": (
            chat_message.attachment.url
            if chat_message.attachment
            else None
        ),
    }

    # Send the event after the database transaction commits.
    def broadcast_message():

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                "type": "chat.message",
                "data": message_data,
            },
        )

    transaction.on_commit(broadcast_message)

    # ========================================
    # RETURN JSON FOR AJAX REQUESTS
    # ========================================

    # JavaScript uses this response to confirm success.
    if is_ajax:
        return JsonResponse(
            {
                "success": True,
                "message_id": chat_message.id,
                "message": "Message sent successfully.",
            },
            status=201,
        )

    # ========================================
    # RETURN TO GROUP CHAT
    # ========================================

    # Normal HTML form submissions still redirect.
    return redirect(
        reverse(
            "group_detail",
            kwargs={"group_id": group.id},
        ) + "#group-chat"
    )

@login_required
@require_POST
def edit_group_message(request, group_id, message_id):
    """Edit a message and broadcast the change through WebSockets."""
# DEBUG: Check whether Django recognizes the AJAX request.
    print("EDIT REQUEST RECEIVED")
    print("AJAX HEADER:", request.headers.get("X-Requested-With"))
    # ========================================
    # 1. CHECK IF REQUEST COMES FROM JAVASCRIPT
    # ========================================

    # AJAX requests receive JSON instead of redirects.
# Check whether JavaScript sent this request.
    is_ajax = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )   

    # ========================================
    # 2. FIND THE GROUP
    # ========================================

    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
    )

    # Only group members can edit messages.
    if not is_group_member(group, request.user):
        return HttpResponseForbidden(
            "You must be a group member to edit messages."
        )

    # ========================================
    # 3. FIND THE MESSAGE
    # ========================================

    chat_message = get_object_or_404(
        GroupChatMessage,
        id=message_id,
        group=group,
    )

    # Only the sender can edit their message.
    if chat_message.sender_id != request.user.id:
        return HttpResponseForbidden(
            "You can only edit your own messages."
        )

    # ========================================
    # 4. CHECK MESSAGE TYPE
    # ========================================

    # Only text messages can be edited.
    if chat_message.message_type != "text":

        if is_ajax:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Only text messages can be edited.",
                },
                status=400,
            )

        messages.error(
            request,
            "Only text messages can be edited.",
        )

        return redirect(
            reverse(
                "group_detail",
                kwargs={"group_id": group.id},
            ) + "#group-chat"
        )

    # ========================================
    # 5. VALIDATE THE NEW CONTENT
    # ========================================

    new_content = request.POST.get(
        "content",
        "",
    ).strip()

    # Prevent empty messages.
    if not new_content:

        if is_ajax:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Your message cannot be empty.",
                },
                status=400,
            )

        messages.error(
            request,
            "Your message cannot be empty.",
        )

        return redirect(
            reverse(
                "group_detail",
                kwargs={"group_id": group.id},
            ) + "#group-chat"
        )

    # ========================================
    # 6. UPDATE THE MESSAGE
    # ========================================

    # Replace the previous message content.
    chat_message.content = new_content

    # Record when the message was edited.
    chat_message.edited_at = timezone.now()

    # Save both changed fields to PostgreSQL.
    chat_message.save(
        update_fields=[
            "content",
            "edited_at",
        ],
    )

    # ========================================
    # 7. BROADCAST THE EDIT THROUGH WEBSOCKETS
    # ========================================

    # Get the Django Channels communication layer.
    channel_layer = get_channel_layer()

    # Use the same group name as consumers.py.
    room_group_name = f"group_chat_{group.id}"

    # Prepare the updated message information.
    message_data = {
        "type": "message_edited",
        "message_id": chat_message.id,
        "group_id": group.id,
        "content": chat_message.content,
        "edited_at": chat_message.edited_at.isoformat(),
    }

    # Broadcast only after the database transaction commits.
    def broadcast_edit():

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                "type": "chat.message",
                "data": message_data,
            },
        )

    transaction.on_commit(broadcast_edit)

    # ========================================
    # 8. RETURN JSON FOR AJAX REQUESTS
    # ========================================

    if is_ajax:
        return JsonResponse(
            {
                "success": True,
                "message_id": chat_message.id,
                "content": chat_message.content,
                "edited_at": chat_message.edited_at.isoformat(),
                "message": "Message updated successfully.",
            },
            status=200,
        )

    # ========================================
    # 9. RETURN TO GROUP CHAT
    # ========================================

    messages.success(
        request,
        "Message updated successfully.",
    )

    return redirect(
        reverse(
            "group_detail",
            kwargs={"group_id": group.id},
        ) + "#group-chat"
    )

# ============================================================
# 18. DELETE GROUP CHAT MESSAGE
#@login_required
@require_POST
def delete_group_message(request, group_id, message_id):
    """Permanently delete a message and broadcast the deletion."""

    # ========================================
    # 1. CHECK IF REQUEST COMES FROM JAVASCRIPT
    # ========================================

    # AJAX requests receive JSON instead of redirects.
    is_ajax = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )

    # ========================================
    # 2. FIND THE GROUP
    # ========================================

    group = get_object_or_404(
        ProjectGroup,
        id=group_id,
    )

    # Only group members can delete messages.
    if not is_group_member(group, request.user):
        return HttpResponseForbidden(
            "You must be a group member to delete messages."
        )

    # ========================================
    # 3. FIND THE MESSAGE
    # ========================================

    chat_message = get_object_or_404(
        GroupChatMessage,
        id=message_id,
        group=group,
    )

    # Only the original sender can delete the message.
    if chat_message.sender_id != request.user.id:
        return HttpResponseForbidden(
            "You can only delete your own messages."
        )

    # ========================================
    # 4. SAVE THE MESSAGE ID BEFORE DELETION
    # ========================================

    # We need this ID to tell connected browsers
    # which message should disappear.
    deleted_message_id = chat_message.id

    # ========================================
    # 5. DELETE THE MESSAGE
    # ========================================

    # Permanently remove the message from PostgreSQL.
    chat_message.delete()

    # ========================================
    # 6. BROADCAST DELETION THROUGH WEBSOCKETS
    # ========================================

    # Get the Django Channels communication layer.
    channel_layer = get_channel_layer()

    # Must match the group name in consumers.py.
    room_group_name = f"group_chat_{group.id}"

    # Prepare the deletion event.
    message_data = {
        "type": "message_deleted",
        "message_id": deleted_message_id,
        "group_id": group.id,
    }

    # Broadcast only after the database transaction commits.
    def broadcast_deletion():

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                "type": "chat.message",
                "data": message_data,
            },
        )

    transaction.on_commit(broadcast_deletion)

    # ========================================
    # 7. RETURN JSON FOR AJAX REQUESTS
    # ========================================

    # JavaScript receives confirmation without reloading.
    if is_ajax:
        return JsonResponse(
            {
                "success": True,
                "message_id": deleted_message_id,
                "message": "Message deleted successfully.",
            },
            status=200,
        )

    # ========================================
    # 8. RETURN TO GROUP CHAT
    # ========================================

    # Keep the original behavior for normal HTML forms.
    messages.success(
        request,
        "Message deleted successfully.",
    )

    return redirect(
        reverse(
            "group_detail",
            kwargs={"group_id": group.id},
        ) + "#group-chat"
    )
    # Send the event after the database transaction commits.
    def broadcast_deletion():
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                # Calls chat_message() inside consumers.py.
                "type": "chat.message",

                # Information sent to connected browsers.
                "data": message_data,
            },
        )

    transaction.on_commit(broadcast_deletion)

    # ========================================
    # 6. RETURN TO GROUP CHAT
    # ========================================

    messages.success(
        request,
        "Message deleted successfully.",
    )

    return redirect(
        reverse(
            "group_detail",
            kwargs={"group_id": group.id},
        ) + "#group-chat"
    )