from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q

from apps.courses.models import Lesson

from apps.enrollments.models import Enrollment

from .models import LessonProgress

class ProgressError(Exception):
    pass


@transaction.atomic
def start_lesson(
    *,
    learner,
    lesson,
):

    enrollment = (
        Enrollment.objects
        .filter(
            learner=learner,
            course=lesson.section.course,
            status__in=[
                Enrollment.Status.ACTIVE,
                Enrollment.Status.COMPLETED,
            ],
        )
        .first()
    )

    if not enrollment:
        raise ProgressError(
            "You are not enrolled in this course."
        )

    progress, created = (
        LessonProgress.objects.get_or_create(
            learner=learner,
            lesson=lesson,
            defaults={
                "enrollment": enrollment,
                "started_at": timezone.now(),
                "last_accessed_at": timezone.now(),
            },
        )
    )

    if not created:
        progress.last_accessed_at = timezone.now()

        if not progress.started_at:
            progress.started_at = timezone.now()

        progress.save(
            update_fields=[
                "started_at",
                "last_accessed_at",
                "updated_at",
            ]
        )

    return progress


@transaction.atomic
def complete_lesson(
    *,
    learner,
    lesson,
):

    enrollment = (
        Enrollment.objects
        .filter(
            learner=learner,
            course=lesson.section.course,
            status__in=[
                Enrollment.Status.ACTIVE,
                Enrollment.Status.COMPLETED,
            ],
        )
        .first()
    )

    if not enrollment:
        raise ProgressError(
            "You are not enrolled in this course."
        )

    progress = (
        LessonProgress.objects
        .filter(
            learner=learner,
            lesson=lesson,
        )
        .first()
    )

    if not progress:
        raise ProgressError(
            "You must start the lesson before completing it."
        )

    if not progress.started_at:
        raise ProgressError(
            "You must start the lesson before completing it."
        )

    now = timezone.now()

    progress.completed = True
    progress.completed_at = (
        progress.completed_at or now
    )
    progress.last_accessed_at = now

    update_enrollment_completion(
        enrollment=enrollment,
    )

    progress.save(
        update_fields=[
            "completed",
            "completed_at",
            "last_accessed_at",
            "updated_at",
        ]
    )

    return progress


def get_course_progress(
    *,
    learner,
    course,
):
    total_lessons = Lesson.objects.filter(
        section__course=course,
    ).count()

    completed_lessons = Lesson.objects.filter(
        section__course=course,
        learner_progress__learner=learner,
        learner_progress__completed=True,
    ).count()

    if total_lessons == 0:
        percentage = 0.0
    else:
        percentage = round(
            (completed_lessons / total_lessons) * 100,
            2,
        )

    return {
        "course_id": course.id,
        "course_title": course.title,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "progress_percentage": percentage,
        "is_completed": (
            total_lessons > 0
            and completed_lessons == total_lessons
        ),
    }


def update_enrollment_completion(
    *,
    enrollment,
):
    total_lessons = Lesson.objects.filter(
        section__course=enrollment.course,
    ).count()

    completed_lessons = Lesson.objects.filter(
        section__course=enrollment.course,
        learner_progress__learner=enrollment.learner,
        learner_progress__completed=True,
    ).count()

    if (
        total_lessons > 0
        and completed_lessons == total_lessons
        and enrollment.status
        == Enrollment.Status.ACTIVE
    ):
        enrollment.status = (
            Enrollment.Status.COMPLETED
        )

        enrollment.completed_at = timezone.now()

        enrollment.save(
            update_fields=[
                "status",
                "completed_at",
                "updated_at",
            ]
        )

        return True

    return False