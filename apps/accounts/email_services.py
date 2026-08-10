from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.conf import settings

from .models import User


def generate_user_token(user):
    uid = urlsafe_base64_encode(
        force_bytes(user.pk)
    )

    token = default_token_generator.make_token(user)

    return uid, token


def send_verification_email(
    user,
    raw_token,
):
    verification_url = (
        f"{settings.FRONTEND_URL}"
        f"/verify-email/{raw_token}/"
    )

    subject = (
        "Verify your Online Learning Platform account"
    )

    message = (
        f"Hello {user.first_name},\n\n"
        f"Thank you for registering.\n\n"
        f"Please verify your email address by "
        f"opening this link:\n\n"
        f"{verification_url}\n\n"
        f"This verification link expires in 24 hours.\n\n"
        f"If you did not create this account, "
        f"you can safely ignore this email.\n\n"
        f"Online Learning Platform"
    )

    recipient = user.email
    print(f"DEBUG: User object: {user}")
    print(f"DEBUG: User email: {user.email}")
    print(f"DEBUG: Recipient list: {[recipient]}")
    print(f"DEBUG: From email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"DEBUG: EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )


def send_password_reset_email(
    user,
    raw_token,
):
    reset_url = (
        f"{settings.FRONTEND_URL}"
        f"/reset-password/{raw_token}/"
    )

    subject = (
        "Reset your Online Learning Platform password"
    )

    message = (
        f"Hello {user.first_name},\n\n"
        f"You requested a password reset.\n\n"
        f"Please open this link to create a new password:\n\n"
        f"{reset_url}\n\n"
        f"This password reset link expires in 1 hour.\n\n"
        f"If you did not request this, "
        f"you can safely ignore this email.\n\n"
        f"Online Learning Platform"
    )

    print(f"DEBUG: Sending password reset email to: {user.email}")
    print(f"DEBUG: From email: {settings.DEFAULT_FROM_EMAIL}")
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )



