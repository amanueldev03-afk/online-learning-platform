from rest_framework import serializers

from .models import Enrollment


class EnrollmentSerializer(
    serializers.ModelSerializer
):

    course_title = serializers.CharField(
        source="course.title",
        read_only=True,
    )

    learner_email = serializers.EmailField(
        source="learner.email",
        read_only=True,
    )

    class Meta:
        model = Enrollment

        fields = [
            "id",
            "course",
            "course_title",
            "learner_email",
            "status",
            "enrolled_at",
            "completed_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "course_title",
            "learner_email",
            "status",
            "enrolled_at",
            "completed_at",
            "updated_at",
        ]