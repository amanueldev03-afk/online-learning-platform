from rest_framework.permissions import BasePermission

from .models import User


class IsLearner(BasePermission):
    message = "Learner access is required."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.LEARNER
        )


class IsInstructor(BasePermission):
    message = "Instructor access is required."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.INSTRUCTOR
        )


class IsAdministrator(BasePermission):
    message = "Administrator access is required."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
        )