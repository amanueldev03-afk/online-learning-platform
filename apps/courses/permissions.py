from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class IsInstructor(BasePermission):
    """
    Only instructors can create courses.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.INSTRUCTOR
        )


class IsCourseOwnerOrAdmin(BasePermission):
    """
    Instructors can modify their own courses.
    Administrators can modify any course.
    """

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        if not request.user.is_authenticated:
            return False

        if request.user.role == User.Role.ADMIN:
            return True

        return (
            request.user.role == User.Role.INSTRUCTOR
            and obj.instructor_id == request.user.id
        )