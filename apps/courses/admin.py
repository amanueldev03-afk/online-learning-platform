from django.contrib import admin
from .models import Course, CourseSection, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "instructor",
        "category",
        "level",
        "status",
        "is_free",
        "price",
        "created_at",
    ]
    list_filter = [
        "status",
        "level",
        "category",
        "is_free",
        "language",
        "created_at",
    ]
    search_fields = [
        "title",
        "short_description",
        "description",
        "instructor__email",
        "instructor__first_name",
        "instructor__last_name",
    ]
    readonly_fields = [
        "slug",
        "published_at",
        "created_at",
        "updated_at",
    ]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "instructor",
                    "title",
                    "slug",
                    "short_description",
                    "description",
                    "thumbnail",
                )
            },
        ),
        (
            "Course Details",
            {
                "fields": (
                    "category",
                    "level",
                    "language",
                    "price",
                    "is_free",
                )
            },
        ),
        (
            "Content",
            {
                "fields": (
                    "requirements",
                    "learning_objectives",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "status",
                    "published_at",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    ordering = ["-created_at"]


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "course",
        "order",
        "is_published",
        "created_at",
    ]
    list_filter = [
        "is_published",
        "created_at",
    ]
    search_fields = [
        "title",
        "description",
        "course__title",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
    ]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "course",
                    "title",
                    "description",
                )
            },
        ),
        (
            "Settings",
            {
                "fields": (
                    "order",
                    "is_published",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    ordering = ["course", "order"]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "section",
        "content_type",
        "order",
        "is_free_preview",
        "is_published",
        "duration_minutes",
        "created_at",
    ]
    list_filter = [
        "content_type",
        "is_free_preview",
        "is_published",
        "created_at",
    ]
    search_fields = [
        "title",
        "description",
        "section__title",
        "section__course__title",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
    ]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "section",
                    "title",
                    "description",
                )
            },
        ),
        (
            "Content",
            {
                "fields": (
                    "content_type",
                    "video_url",
                    "article_content",
                    "document",
                    "external_url",
                )
            },
        ),
        (
            "Settings",
            {
                "fields": (
                    "duration_minutes",
                    "order",
                    "is_free_preview",
                    "is_published",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    ordering = ["section", "order"]
