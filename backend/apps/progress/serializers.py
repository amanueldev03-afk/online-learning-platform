from rest_framework import serializers

from .models import LessonProgress


class LessonProgressSerializer(
    serializers.ModelSerializer
):

    lesson_title = serializers.CharField(
        source="lesson.title",
        read_only=True,
    )

    course_id = serializers.IntegerField(
        source="lesson.section.course.id",
        read_only=True,
    )

    class Meta:
        model = LessonProgress

        fields = [
            "id",
            "lesson",
            "lesson_title",
            "course_id",
            "completed",
            "started_at",
            "completed_at",
            "last_accessed_at",
            "updated_at",
        ]

        read_only_fields = fields


class CourseProgressSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    course_title = serializers.CharField()
    total_lessons = serializers.IntegerField()
    completed_lessons = serializers.IntegerField()
    progress_percentage = serializers.FloatField()
    is_completed = serializers.BooleanField()