from django.db import transaction

from allauth.socialaccount.models import SocialAccount
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    InstructorProfile,
    LearnerProfile,
    User,
)


@transaction.atomic
def get_or_create_google_user(
    *,
    email,
    first_name="",
    last_name="",
    google_id,
    role=None,
):
    """
    Find an existing user by email or create a new
    Google-authenticated user.

    Existing users keep their existing application role.
    New users must provide LEARNER or INSTRUCTOR.
    """

    email = email.lower().strip()

    user = (
        User.objects
        .select_for_update()
        .filter(email__iexact=email)
        .first()
    )

    # Existing user
    if user:

        if not user.is_active:
            raise ValueError(
                "This account is inactive."
            )

        return user, False

    # New user requires role
    if role not in {
        User.Role.LEARNER,
        User.Role.INSTRUCTOR,
    }:
        raise ValueError(
            "A valid learner or instructor role is required."
        )

    user = User.objects.create_user(
        email=email,
        password=None,
        first_name=first_name or "",
        last_name=last_name or "",
        role=role,
    )

    # Google has already verified the identity/email.
    user.email_verified = True

    user.save(
        update_fields=["email_verified"]
    )

    if role == User.Role.LEARNER:
        LearnerProfile.objects.create(
            user=user
        )

    elif role == User.Role.INSTRUCTOR:
        InstructorProfile.objects.create(
            user=user
        )

    return user, True


@transaction.atomic
def link_google_account(
    *,
    user,
    google_id,
):
    """
    Link a Google identity to an existing application user.
    """

    existing_social_account = (
        SocialAccount.objects
        .filter(
            provider="google",
            uid=google_id,
        )
        .first()
    )

    if existing_social_account:

        if existing_social_account.user_id != user.id:
            raise ValueError(
                "This Google account is already linked "
                "to another account."
            )

        return existing_social_account

    # Check whether this user already has another Google account.
    user_google_account = (
        SocialAccount.objects
        .filter(
            user=user,
            provider="google",
        )
        .first()
    )

    if user_google_account:

        if user_google_account.uid != google_id:
            raise ValueError(
                "Another Google account is already linked "
                "to this user."
            )

        return user_google_account

    return SocialAccount.objects.create(
        user=user,
        provider="google",
        uid=google_id,
    )


def create_google_jwt_tokens(user):
    """
    Convert our authenticated Django user into
    application JWT tokens.
    """

    refresh = RefreshToken.for_user(user)

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }