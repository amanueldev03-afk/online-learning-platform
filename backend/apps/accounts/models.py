from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

import uuid

from django.conf import settings

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        LEARNER = "LEARNER", "Learner"
        INSTRUCTOR = "INSTRUCTOR", "Instructor"
        ADMIN = "ADMIN", "Administrator"

    email = models.EmailField(
        unique=True,
        db_index=True,
    )

    first_name = models.CharField(
        max_length=100,
    )

    last_name = models.CharField(
        max_length=100,
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.LEARNER,
        db_index=True,
    )

    email_verified = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_staff = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
    ]

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()



class LearnerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="learner_profile",
    )

    profile_photo = models.ImageField(
        upload_to="profiles/learners/",
        blank=True,
        null=True,
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
    )

    country = models.CharField(
        max_length=100,
        blank=True,
    )

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True,
    )

    bio = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"Learner profile - {self.user.email}"


class InstructorProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="instructor_profile",
    )

    profile_photo = models.ImageField(
        upload_to="profiles/instructors/",
        blank=True,
        null=True,
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
    )

    specialization = models.CharField(
        max_length=255,
        blank=True,
    )

    experience_years = models.PositiveIntegerField(
        default=0,
    )

    bio = models.TextField(
        blank=True,
    )

    website = models.URLField(
        blank=True,
    )

    linkedin = models.URLField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"Instructor profile - {self.user.email}"



class EmailVerificationToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )

    token_hash = models.CharField(
        max_length=128,
        unique=True,
    )

    expires_at = models.DateTimeField()

    used_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "expires_at"]
            ),
        ]

    def __str__(self):
        return (
            f"Email verification token "
            f"for {self.user.email}"
        )

    @property
    def is_used(self):
        return self.used_at is not None


class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )

    token_hash = models.CharField(
        max_length=128,
        unique=True,
    )

    expires_at = models.DateTimeField()

    used_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "expires_at"]
            ),
        ]

    def __str__(self):
        return (
            f"Password reset token "
            f"for {self.user.email}"
        )

    @property
    def is_used(self):
        return self.used_at is not None