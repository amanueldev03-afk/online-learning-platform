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
        help_text="Password for the account (min 8 characters)"
    )

    password_confirm = serializers.CharField(
        write_only=True,
        help_text="Confirm password (must match password)"
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
        extra_kwargs = {
            "email": {"help_text": "User email address"},
            "first_name": {"help_text": "User first name"},
            "last_name": {"help_text": "User last name"},
            "role": {"help_text": "User role (LEARNER or INSTRUCTOR)"},
        }

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
    email = serializers.EmailField(
        help_text="User email address"
    )
    password = serializers.CharField(
        write_only=True,
        help_text="User password"
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

        if not user.email_verified:
            raise serializers.ValidationError(
                "Please verify your email address before logging in."
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
        extra_kwargs = {
            "profile_photo": {"help_text": "Profile photo URL"},
            "phone": {"help_text": "Phone number"},
            "country": {"help_text": "Country name"},
            "city": {"help_text": "City name"},
            "date_of_birth": {"help_text": "Date of birth"},
            "bio": {"help_text": "Short biography"},
        }


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
        extra_kwargs = {
            "profile_photo": {"help_text": "Profile photo URL"},
            "phone": {"help_text": "Phone number"},
            "specialization": {"help_text": "Area of specialization"},
            "experience_years": {"help_text": "Years of experience"},
            "bio": {"help_text": "Professional biography"},
            "website": {"help_text": "Personal website URL"},
            "linkedin": {"help_text": "LinkedIn profile URL"},
        }


class EmailVerificationSerializer(
    serializers.Serializer
):
    token = serializers.CharField(
        help_text="Email verification token received in email"
    )

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
    email = serializers.EmailField(
        help_text="Email address to resend verification"
    )

    def validate_email(self, value):
        return value.lower().strip()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="Email address for password reset"
    )

    def validate_email(self, value):
        return value.lower().strip()



class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(
        help_text="Password reset token received in email"
    )

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text="New password (min 8 characters)"
    )

    password_confirm = serializers.CharField(
        write_only=True,
        help_text="Confirm new password (must match password)"
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
        ],
        help_text="User role for Google login"
    )


class GoogleLoginSerializer(serializers.Serializer):
    credential = serializers.CharField(
        write_only=True,
        help_text="Google OAuth credential token"
    )

    role = serializers.ChoiceField(
        choices=[
            User.Role.LEARNER,
            User.Role.INSTRUCTOR,
        ],
        required=False,
        help_text="User role (required for new accounts)"
    )


class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="Admin email address"
    )
    password = serializers.CharField(
        help_text="Admin password",
        style={"input_type": "password"},
        write_only=True,
    )