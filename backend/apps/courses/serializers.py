from rest_framework import serializers

from .models import (
    Course,
    CourseSection,
    Lesson,
    )


class CourseSerializer(serializers.ModelSerializer):

    instructor_name = serializers.CharField(
        source="instructor.get_full_name",
        read_only=True,
    )

    category_name = serializers.CharField(
        source="category.name",
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
            "category_name",
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
        extra_kwargs = {
            "title": {"help_text": "Course title"},
            "slug": {"help_text": "URL-friendly course identifier (auto-generated from title)"},
            "short_description": {"help_text": "Brief course description (max 500 characters)"},
            "description": {"help_text": "Detailed course description"},
            "thumbnail": {"help_text": "Course thumbnail image"},
            "category": {"help_text": "Course category"},
            "level": {"help_text": "Course difficulty level (BEGINNER, INTERMEDIATE, ADVANCED)"},
            "language": {"help_text": "Course language (default: English)"},
            "price": {"help_text": "Course price (0 for free courses)"},
            "is_free": {"help_text": "Whether the course is free"},
            "requirements": {"help_text": "Course prerequisites"},
            "learning_objectives": {"help_text": "Learning objectives and goals"},
        }

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
        extra_kwargs = {
            "title": {"help_text": "Section title"},
            "description": {"help_text": "Section description"},
            "order": {"help_text": "Section order (must be non-negative)"},
            "is_published": {"help_text": "Whether the section is published"},
        }

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
        extra_kwargs = {
            "title": {"help_text": "Lesson title"},
            "description": {"help_text": "Lesson description"},
            "content_type": {"help_text": "Content type (VIDEO, ARTICLE, DOCUMENT, EXTERNAL)"},
            "video_url": {"help_text": "Video URL (required for VIDEO type)"},
            "article_content": {"help_text": "Article content (required for ARTICLE type)"},
            "document": {"help_text": "Document file (required for DOCUMENT type)"},
            "external_url": {"help_text": "External resource URL (required for EXTERNAL type)"},
            "duration_minutes": {"help_text": "Lesson duration in minutes"},
            "order": {"help_text": "Lesson order within section"},
            "is_free_preview": {"help_text": "Whether this lesson is available as free preview"},
            "is_published": {"help_text": "Whether the lesson is published"},
        }

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



class LessonPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "description",
            "content_type",
            "video_url",
            "article_content",
            "duration_minutes",
            "order",
            "is_free_preview",
        ]


class CourseSectionPublicSerializer(serializers.ModelSerializer):
    lessons = LessonPublicSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = CourseSection
        fields = [
            "id",
            "title",
            "description",
            "order",
            "lessons",
        ]


class CourseCurriculumSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(
        source="instructor.full_name",
        read_only=True,
    )

    sections = CourseSectionPublicSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "short_description",
            "description",
            "thumbnail",
            "category",
            "level",
            "language",
            "requirements",
            "learning_objectives",
            "instructor_name",
            "sections",
        ]