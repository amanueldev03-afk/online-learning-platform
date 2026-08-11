from rest_framework import serializers

from .models import (
    Course,
    CourseSection,
    Lesson,
    )


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



class CourseSectionSerializer(serializers.ModelSerializer):

    course_title = serializers.CharField(
        source="course.title",
        read_only=True,
    )

    class Meta:
        model = CourseSection

        fields = [
            "id",
            "course",
            "course_title",
            "title",
            "description",
            "order",
            "is_published",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "course",
            "course_title",
            "created_at",
            "updated_at",
        ]

    def validate_order(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Section order cannot be negative."
            )

        return value



class LessonSerializer(serializers.ModelSerializer):

    section_title = serializers.CharField(
        source="section.title",
        read_only=True,
    )

    class Meta:
        model = Lesson

        fields = [
            "id",
            "section",
            "section_title",
            "title",
            "description",
            "content_type",
            "video_url",
            "article_content",
            "document",
            "external_url",
            "duration_minutes",
            "order",
            "is_free_preview",
            "is_published",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "section",
            "section_title",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        content_type = attrs.get(
            "content_type",
            getattr(
                self.instance,
                "content_type",
                None,
            ),
        )

        video_url = attrs.get(
            "video_url",
            getattr(
                self.instance,
                "video_url",
                "",
            ),
        )

        article_content = attrs.get(
            "article_content",
            getattr(
                self.instance,
                "article_content",
                "",
            ),
        )

        document = attrs.get(
            "document",
            getattr(
                self.instance,
                "document",
                None,
            ),
        )

        external_url = attrs.get(
            "external_url",
            getattr(
                self.instance,
                "external_url",
                "",
            ),
        )

        if content_type == Lesson.ContentType.VIDEO:
            if not video_url:
                raise serializers.ValidationError({
                    "video_url": (
                        "Video URL is required for video lessons."
                    )
                })

        elif content_type == Lesson.ContentType.ARTICLE:
            if not article_content:
                raise serializers.ValidationError({
                    "article_content": (
                        "Article content is required "
                        "for article lessons."
                    )
                })

        elif content_type == Lesson.ContentType.DOCUMENT:
            if not document:
                raise serializers.ValidationError({
                    "document": (
                        "Document is required "
                        "for document lessons."
                    )
                })

        elif content_type == Lesson.ContentType.EXTERNAL:
            if not external_url:
                raise serializers.ValidationError({
                    "external_url": (
                        "External URL is required "
                        "for external lessons."
                    )
                })

        return attrs