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

class IsEmailVerified(BasePermission):
    message = "Please verify your email address."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.email_verified
        )


class IsAdminOrOwner(BasePermission):
    """
    Base permission class that allows admin access or owner access.
    Subclasses must implement get_owner_id method.
    """
    message = "You do not have permission to perform this action."

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.user.role == User.Role.ADMIN:
            return True

        owner_id = self.get_owner_id(obj)
        return request.user.id == owner_id

    def get_owner_id(self, obj):
        """Override this method to return the owner ID of the object."""
        raise NotImplementedError("Subclasses must implement get_owner_id")


class IsAdminOrInstructor(BasePermission):
    """
    Allows access to admins or instructors.
    """
    message = "Only administrators or instructors can perform this action."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.role in [User.Role.ADMIN, User.Role.INSTRUCTOR]


class IsAdminOrInstructorOwner(BasePermission):
    """
    Allows admin access or instructor if they own the related course.
    Used for sections and lessons where ownership is through the course.
    """
    message = "You do not have permission to perform this action."

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.user.role == User.Role.ADMIN:
            return True

        if request.user.role == User.Role.INSTRUCTOR:
            # Get the course instructor ID from the object
            course_instructor_id = self.get_course_instructor_id(obj)
            return request.user.id == course_instructor_id

        return False

    def get_course_instructor_id(self, obj):
        """Override this method to return the course instructor ID."""
        raise NotImplementedError("Subclasses must implement get_course_instructor_id")