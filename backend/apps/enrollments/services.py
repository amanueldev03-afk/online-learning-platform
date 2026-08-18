from django.db import transaction

from .models import Enrollment


class EnrollmentError(Exception):
    pass


@transaction.atomic
def enroll_learner(
    *,
    learner,
    course,
):

    if learner.role != learner.Role.LEARNER:
        raise EnrollmentError(
            "Only learners can enroll in courses."
        )

    if course.status != course.Status.PUBLISHED:
        raise EnrollmentError(
            "Only published courses can be enrolled in."
        )

    enrollment = Enrollment.objects.filter(
        learner=learner,
        course=course,
    ).first()

    if enrollment:
        if (
            enrollment.status
            == Enrollment.Status.CANCELLED
        ):
            enrollment.status = (
                Enrollment.Status.ACTIVE
            )

            enrollment.completed_at = None

            enrollment.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "updated_at",
                ]
            )

            return enrollment

        raise EnrollmentError(
            "You are already enrolled in this course."
        )

    return Enrollment.objects.create(
        learner=learner,
        course=course,
    )