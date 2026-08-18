from django.urls import path

from .views import (
    AdminLoginView,
    LoginView,
    LogoutView,
    MeView,
    MyProfileView,
    RegisterView,
    VerifyEmailView,
    ResendVerificationView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    GoogleLoginView,
)

app_name = "accounts"

urlpatterns = [
    path(
        "register/",
        RegisterView.as_view(),
        name="register",
    ),
    path(
        "login/",
        LoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),
    path(
        "me/",
        MeView.as_view(),
        name="me",
    ),
    path(
        "profile/",
        MyProfileView.as_view(),
        name="profile",
    ),
    path(
        "verify-email/",
        VerifyEmailView.as_view(),
        name="verify-email",
    ),
    path(
        "resend-verification/",
        ResendVerificationView.as_view(),
        name="resend-verification",
    ),
    path(
        "forgot-password/",
        PasswordResetRequestView.as_view(),
        name="forgot-password",
    ),
    path(
        "reset-password/",
        PasswordResetConfirmView.as_view(),
        name="reset-password",
    ),
    path(
        "google/",
        GoogleLoginView.as_view(),
        name="google-login",
    ),
    path(
        "admin/login/",
        AdminLoginView.as_view(),
        name="admin-login",
    ),
]