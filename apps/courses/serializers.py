from rest_framework import serializers

from .models import Course


class CourseSerializer(serializers.ModelSerializer):

    instructor_name = serializers.CharField(
        source="instructor.full_name",
        read_only=True,
    )

    class Meta:
        model = Course

        fields = [
            "id",
            "instructor",
            "instructor_name",
            "title",
            "slug",
            "short_description",
            "description",
            "thumbnail",
            "category",
            "level",
            "language",
            "price",
            "is_free",
            "requirements",
            "learning_objectives",
            "status",
            "published_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "instructor",
            "instructor_name",
            "published_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        is_free = attrs.get(
            "is_free",
            getattr(
                self.instance,
                "is_free",
                True,
            ),
        )

        price = attrs.get(
            "price",
            getattr(
                self.instance,
                "price",
                0,
            ),
        )

        if is_free and price != 0:
            raise serializers.ValidationError(
                {
                    "price": (
                        "Free courses must have a price of 0."
                    )
                }
            )

        if not is_free and price <= 0:
            raise serializers.ValidationError(
                {
                    "price": (
                        "Paid courses must have a price greater than 0."
                    )
                }
            )

        return attrs