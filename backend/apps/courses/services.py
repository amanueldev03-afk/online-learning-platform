from django.db import transaction
from django.utils import timezone

from .models import Course


class CoursePublishError(Exception):
    """Raised when a course cannot be published."""


@transaction.atomic
def publish_course(course):
    """
    Publish a course after validating its required information.
    """

    if course.status == Course.Status.PUBLISHED:
        return course

    if course.status == Course.Status.ARCHIVED:
        raise CoursePublishError(
            "Archived courses cannot be published."
        )

    if not course.title.strip():
        raise CoursePublishError(
            "Course title is required."
        )

    if not course.short_description.strip():
        raise CoursePublishError(
            "Short description is required."
        )

    if not course.description.strip():
        raise CoursePublishError(
            "Course description is required."
        )

    if not course.category:
        raise CoursePublishError(
            "Course category is required."
        )

    if not course.learning_objectives.strip():
        raise CoursePublishError(
            "Learning objectives are required."
        )

    if course.is_free and course.price != 0:
        raise CoursePublishError(
            "Free courses must have a price of 0."
        )

    if not course.is_free and course.price <= 0:
        raise CoursePublishError(
            "Paid courses must have a price greater than 0."
        )

    course.status = Course.Status.PUBLISHED
    course.published_at = timezone.now()

    course.save(
        update_fields=[
            "status",
            "published_at",
            "updated_at",
        ]
    )

    return course


@transaction.atomic
def archive_course(course):
    """
    Archive a published course.
    """

    if course.status == Course.Status.ARCHIVED:
        return course

    course.status = Course.Status.ARCHIVED

    course.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return course