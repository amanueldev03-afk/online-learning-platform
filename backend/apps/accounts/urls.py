from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    MeView,
    MyProfileView,
    RegisterView,
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
]