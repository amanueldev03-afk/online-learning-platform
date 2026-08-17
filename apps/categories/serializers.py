from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):

    parent_name = serializers.CharField(
        source="parent.name",
        read_only=True,
    )

    class Meta:
        model = Category

        fields = [
            "id",
            "name",
            "slug",
            "description",
            "parent",
            "parent_name",
            "image",
            "is_active",
            "display_order",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "slug",
            "parent_name",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "name": {"help_text": "Category name"},
            "slug": {"help_text": "URL-friendly slug"},
            "description": {"help_text": "Category description"},
            "parent": {"help_text": "Parent category for hierarchical structure"},
            "image": {"help_text": "Category image"},
            "is_active": {"help_text": "Whether the category is active"},
            "display_order": {"help_text": "Order for display"},
        }

    def validate_parent(self, value):

        if self.instance and value:
            if value.id == self.instance.id:
                raise serializers.ValidationError(
                    "A category cannot be its own parent."
                )

        return value