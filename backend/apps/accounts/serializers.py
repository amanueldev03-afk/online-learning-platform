from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import (
    InstructorProfile,
    LearnerProfile,
    User,
)

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