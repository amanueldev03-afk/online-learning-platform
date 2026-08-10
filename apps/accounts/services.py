from django.db import transaction

from .models import (
    EmailVerificationToken,
    InstructorProfile,
    LearnerProfile,
    PasswordResetToken,
    User,
)

import hashlib

import secrets

from datetime import timedelta

from django.utils import timezone

from rest_framework_simplejwt.tokens import RefreshToken

from .email_services import send_verification_email

from .tasks import send_verification_email_task


@transaction.atomic
def create_user(
    *,
    email,
    password,
    first_name,
    last_name,
    role,
):
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=role,
    )

    if role == User.Role.LEARNER:
        LearnerProfile.objects.create(
            user=user,
        )

    elif role == User.Role.INSTRUCTOR:
        InstructorProfile.objects.create(
            user=user,
        )

    raw_token, _ = create_verification_token(
        user
    )

    transaction.on_commit(
        lambda: send_verification_email_task.delay(
            user.id,
            raw_token,
        )
    )

    return user


def generate_tokens(user):
    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }



def generate_verification_token(user):
    raw_token = secrets.token_urlsafe(48)

    token_hash = hashlib.sha256(
        raw_token.encode()
    ).hexdigest()

    verification_token = (
        EmailVerificationToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=(
                timezone.now()
                + timedelta(hours=24)
            ),
        )
    )

    return raw_token, verification_token


def invalidate_verification_tokens(user):
    EmailVerificationToken.objects.filter(
        user=user,
        used_at__isnull=True,
    ).update(
        used_at=timezone.now()
    )

def create_verification_token(user):
    invalidate_verification_tokens(user)

    raw_token, verification_token = (
        generate_verification_token(user)
    )

    return raw_token, verification_token


def generate_password_reset_token(user):
    raw_token = secrets.token_urlsafe(48)

    token_hash = hashlib.sha256(
        raw_token.encode()
    ).hexdigest()

    reset_token = (
        PasswordResetToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=(
                timezone.now()
                + timedelta(hours=1)
            ),
        )
    )

    return raw_token, reset_token


def invalidate_password_reset_tokens(user):
    PasswordResetToken.objects.filter(
        user=user,
        used_at__isnull=True,
    ).update(
        used_at=timezone.now()
    )


def create_password_reset_token(user):
    invalidate_password_reset_tokens(user)

    raw_token, reset_token = (
        generate_password_reset_token(user)
    )

    return raw_token, reset_token