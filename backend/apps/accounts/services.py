from django.db import transaction

from .models import (
    InstructorProfile,
    LearnerProfile,
    User,
)

from rest_framework_simplejwt.tokens import RefreshToken


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

    return user


def generate_tokens(user):
    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }