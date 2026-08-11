from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Course(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        ARCHIVED = "ARCHIVED", "Archived"

    class Level(models.TextChoices):
        BEGINNER = "BEGINNER", "Beginner"
        INTERMEDIATE = "INTERMEDIATE", "Intermediate"
        ADVANCED = "ADVANCED", "Advanced"

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses",
    )

    title = models.CharField(
        max_length=255,
    )

    slug = models.SlugField(
        max_length=255,
        unique=True,
    )

    short_description = models.CharField(
        max_length=500,
    )

    description = models.TextField()

    thumbnail = models.ImageField(
        upload_to="courses/thumbnails/",
        blank=True,
        null=True,
    )

    category = models.CharField(
        max_length=100,
    )

    level = models.CharField(
        max_length=20,
        choices=Level.choices,
        default=Level.BEGINNER,
    )

    language = models.CharField(
        max_length=50,
        default="English",
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    is_free = models.BooleanField(
        default=True,
    )

    requirements = models.TextField(
        blank=True,
    )

    learning_objectives = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["category"]),
            models.Index(fields=["level"]),
            models.Index(fields=["instructor"]),
        ]

    def __str__(self):
        return self.title




class CourseSection(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="sections",
    )

    title = models.CharField(
        max_length=255,
    )

    description = models.TextField(
        blank=True,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    is_published = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["order", "created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["course", "order"],
                name="unique_section_order_per_course",
            ),
        ]

        indexes = [
            models.Index(
                fields=["course", "order"],
            ),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.title}"



class Lesson(models.Model):

    class ContentType(models.TextChoices):
        VIDEO = "VIDEO", "Video"
        ARTICLE = "ARTICLE", "Article"
        DOCUMENT = "DOCUMENT", "Document"
        EXTERNAL = "EXTERNAL", "External Resource"

    section = models.ForeignKey(
        CourseSection,
        on_delete=models.CASCADE,
        related_name="lessons",
    )

    title = models.CharField(
        max_length=255,
    )

    description = models.TextField(
        blank=True,
    )

    content_type = models.CharField(
        max_length=20,
        choices=ContentType.choices,
        default=ContentType.VIDEO,
    )

    video_url = models.URLField(
        blank=True,
    )

    article_content = models.TextField(
        blank=True,
    )

    document = models.FileField(
        upload_to="courses/documents/",
        blank=True,
        null=True,
    )

    external_url = models.URLField(
        blank=True,
    )

    duration_minutes = models.PositiveIntegerField(
        default=0,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    is_free_preview = models.BooleanField(
        default=False,
    )

    is_published = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["order", "created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["section", "order"],
                name="unique_lesson_order_per_section",
            ),
        ]

        indexes = [
            models.Index(
                fields=["section", "order"],
            ),
            models.Index(
                fields=["content_type"],
            ),
            models.Index(
                fields=["is_published"],
            ),
        ]

    def __str__(self):
        return f"{self.section.title} - {self.title}"