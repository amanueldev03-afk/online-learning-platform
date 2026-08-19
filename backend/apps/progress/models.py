from django.conf import settings
from django.db import models

from apps.courses.models import Lesson
from apps.enrollments.models import Enrollment


class LessonProgress(models.Model):

    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lesson_progress",
    )

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="lesson_progress",
    )

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="learner_progress",
    )

    completed = models.BooleanField(
        default=False,
        db_index=True,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_accessed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["lesson__order"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "learner",
                    "lesson",
                ],
                name="unique_learner_lesson_progress",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "learner",
                    "completed",
                ],
            ),
            models.Index(
                fields=[
                    "enrollment",
                    "completed",
                ],
            ),
        ]

    def __str__(self):
        return (
            f"{self.learner.email} - "
            f"{self.lesson.title}"
        )