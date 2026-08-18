from django.conf import settings
from django.db import models

from apps.courses.models import Course


class Enrollment(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    enrolled_at = models.DateTimeField(
        auto_now_add=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-enrolled_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["learner", "course"],
                name="unique_learner_course_enrollment",
            ),
        ]

        indexes = [
            models.Index(
                fields=["learner", "status"],
            ),
            models.Index(
                fields=["course", "status"],
            ),
        ]

    def __str__(self):
        return (
            f"{self.learner.email} - "
            f"{self.course.title}"
        )