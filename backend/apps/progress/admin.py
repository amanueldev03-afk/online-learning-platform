from django.contrib import admin

from .models import LessonProgress


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = [
        "learner",
        "lesson",
        "enrollment",
        "completed",
        "started_at",
        "completed_at",
        "last_accessed_at",
    ]
    
    list_filter = [
        "completed",
        "started_at",
        "completed_at",
        "last_accessed_at",
    ]
    
    search_fields = [
        "learner__email",
        "learner__first_name",
        "learner__last_name",
        "lesson__title",
    ]
    
    readonly_fields = [
        "updated_at",
    ]
    
    fieldsets = (
        ("User Information", {
            "fields": ("learner", "enrollment")
        }),
        ("Lesson Information", {
            "fields": ("lesson",)
        }),
        ("Progress Status", {
            "fields": ("completed", "started_at", "completed_at", "last_accessed_at")
        }),
        ("Timestamps", {
            "fields": ("updated_at",),
            "classes": ("collapse",)
        }),
    )
    
    ordering = ["-last_accessed_at"]
