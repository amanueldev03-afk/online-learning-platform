from rest_framework.permissions import BasePermission

from apps.accounts.models import User
from apps.accounts.permissions import IsAdminOrInstructorOwner


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


class IsSectionOwnerOrAdmin(IsAdminOrInstructorOwner):
    """
    Only the course instructor or administrator can modify a section.
    """

    def get_course_instructor_id(self, obj):
        return obj.course.instructor_id


class IsLessonOwnerOrAdmin(IsAdminOrInstructorOwner):
    """
    Only the course instructor or administrator can modify a lesson.
    """

    def get_course_instructor_id(self, obj):
        return obj.section.course.instructor_id