from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

import hashlib

from django.utils import timezone

from .models import (
    EmailVerificationToken,
    InstructorProfile,
    LearnerProfile,
    PasswordResetToken,
    User,
)

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    password_confirm = serializers.CharField(
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "role",
            "password",
            "password_confirm",
        ]

    def validate_email(self, value):
        return value.lower().strip()

    def validate_role(self, value):
        if value == User.Role.ADMIN:
            raise serializers.ValidationError(
                "Administrator accounts cannot be created through public registration."
            )

        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {
                    "password_confirm": "Passwords do not match."
                }
            )

        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
    )

    def validate(self, attrs):
        email = attrs["email"].lower().strip()
        password = attrs["password"]

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )

        if not user:
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "This account is inactive."
            )

        attrs["user"] = user

        return attrs


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "email_verified",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "role",
            "email_verified",
            "created_at",
        ]


class LearnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearnerProfile
        fields = [
            "profile_photo",
            "phone",
            "country",
            "city",
            "date_of_birth",
            "bio",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "created_at",
            "updated_at",
        ]


class InstructorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorProfile
        fields = [
            "profile_photo",
            "phone",
            "specialization",
            "experience_years",
            "bio",
            "website",
            "linkedin",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "created_at",
            "updated_at",
        ]


class EmailVerificationSerializer(
    serializers.Serializer
):
    token = serializers.CharField()

    def validate(self, attrs):
        token = attrs["token"]

        token_hash = hashlib.sha256(
            token.encode()
        ).hexdigest()

        verification = (
            EmailVerificationToken.objects
            .select_related("user")
            .filter(
                token_hash=token_hash,
                used_at__isnull=True,
            )
            .first()
        )

        if not verification:
            raise serializers.ValidationError(
                "Invalid or already used verification token."
            )

        if verification.expires_at <= timezone.now():
            raise serializers.ValidationError(
                "Verification token has expired."
            )

        attrs["verification"] = verification

        return attrs

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()



class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    password_confirm = serializers.CharField(
        write_only=True,
    )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {
                    "password_confirm": (
                        "Passwords do not match."
                    )
                }
            )

        token = attrs["token"]

        token_hash = hashlib.sha256(
            token.encode()
        ).hexdigest()

        reset_token = (
            PasswordResetToken.objects
            .select_related("user")
            .filter(
                token_hash=token_hash,
                used_at__isnull=True,
            )
            .first()
        )

        if not reset_token:
            raise serializers.ValidationError(
                "Invalid or already used password reset token."
            )

        if reset_token.expires_at <= timezone.now():
            raise serializers.ValidationError(
                "Password reset token has expired."
            )

        attrs["reset_token"] = reset_token
        attrs["user"] = reset_token.user

        return attrs



class GoogleRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=[
            User.Role.LEARNER,
            User.Role.INSTRUCTOR,
        ]
    )


class GoogleLoginSerializer(serializers.Serializer):
    credential = serializers.CharField(
        write_only=True
    )

    role = serializers.ChoiceField(
        choices=[
            User.Role.LEARNER,
            User.Role.INSTRUCTOR,
        ],
        required=False,
    )