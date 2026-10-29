"""Authenticate requests sent to the CodeView sandbox controller."""

import os
import secrets

from fastapi import Header, HTTPException, status


def verify_controller_token(
    authorization: str | None = Header(default=None),
):
    """
    Verify that a request contains the correct controller token.

    Only trusted internal services should possess this token.
    """

    # Get the expected token from the environment.
    expected_token = os.environ.get(
        "CODEVIEW_CONTROLLER_TOKEN",
        "",
    )

    # Reject requests if authentication is not configured.
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Controller authentication is not configured.",
        )

    # Reject requests without an Authorization header.
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    # Separate the authentication scheme from the token.
    scheme, separator, supplied_token = authorization.partition(" ")

    # Require the Bearer authentication scheme.
    if (
        not separator
        or scheme.lower() != "bearer"
        or not supplied_token
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication format.",
        )

    # Compare the supplied token with the expected token.
    if not secrets.compare_digest(
        supplied_token,
        expected_token,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid controller token.",
        )

    # Authentication succeeded.
    return True