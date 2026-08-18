from apps.accounts.models import User
from apps.courses.models import Lesson

from .models import Enrollment


def has_course_access(*, user, course):
    """
    Determine whether a user can access
    the complete course.
    """

    if not user or not user.is_authenticated:
        return False

    if user.role in {
        User.Role.ADMIN,
        User.Role.INSTRUCTOR,
    }:
        return True

    return Enrollment.objects.filter(
        learner=user,
        course=course,
        status__in=[
            Enrollment.Status.ACTIVE,
            Enrollment.Status.COMPLETED,
        ],
    ).exists()


def can_access_lesson(*, user, lesson):
    """
    Determine whether a user can access
    a particular lesson.
    """

    if lesson.is_free_preview:
        return True

    return has_course_access(
        user=user,
        course=lesson.section.course,
    )