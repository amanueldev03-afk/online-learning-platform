from django.contrib import admin
from django.utils.html import format_html

from .models import Enrollment


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "learner_email",
        "course_title",
        "status",
        "enrolled_at",
        "completed_at",
        "updated_at",
    ]
    
    list_filter = [
        "status",
        "enrolled_at",
        "completed_at",
    ]
    
    search_fields = [
        "learner__email",
        "course__title",
    ]
    
    readonly_fields = [
        "enrolled_at",
        "updated_at",
    ]
    
    fieldsets = (
        (
            "Enrollment Information",
            {
                "fields": (
                    "learner",
                    "course",
                    "status",
                )
            }
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "enrolled_at",
                    "completed_at",
                    "updated_at",
                )
            }
        ),
    )
    
    def learner_email(self, obj):
        return obj.learner.email
    learner_email.short_description = "Learner Email"
    learner_email.admin_order_field = "learner__email"
    
    def course_title(self, obj):
        return obj.course.title
    course_title.short_description = "Course Title"
    course_title.admin_order_field = "course__title"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "learner",
            "course",
        )
