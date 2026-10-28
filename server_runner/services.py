"""Business logic for CodeView developer terminal sessions."""

# Import Django database transactions.
from django.db import transaction

# Import CodeView's group membership model.
from community.models import GroupMember

# Import our terminal session model.
from server_runner.models import DeveloperTerminalSession


@transaction.atomic
def create_terminal_session(user, group):
    """Create a terminal session for an authenticated group member."""

    # Step 1: Verify that the developer is authenticated.
    if not user.is_authenticated:
        raise PermissionError(
            "You must log in to use the terminal."
        )

    # Step 2: Only allow terminals inside private development groups.
    if not group.is_private:
        raise PermissionError(
            "Terminals are only available in private development groups."
        )

    # Step 3: Check whether the developer owns the group.
    is_owner = group.owner_id == user.pk

    # Step 4: Check whether the developer is an approved group member.
    is_member = GroupMember.objects.filter(
        group=group,
        user=user,
    ).exists()

    # Step 5: Reject developers who are neither owners nor members.
    if not is_owner and not is_member:
        raise PermissionError(
            "You do not have permission to use this group's terminal."
        )

    # Step 6: Create a new terminal session in PostgreSQL.
    session = DeveloperTerminalSession.objects.create(
        developer=user,
        group_id=group.pk,
        status="created",
    )

    # Step 7: Return the newly created session.
    return session