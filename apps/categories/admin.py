from django.contrib import admin
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "parent",
        "is_active",
        "display_order",
        "created_at",
    ]
    list_filter = [
        "is_active",
        "parent",
        "created_at",
    ]
    search_fields = [
        "name",
        "slug",
        "description",
    ]
    readonly_fields = [
        "slug",
        "created_at",
        "updated_at",
    ]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                )
            },
        ),
        (
            "Hierarchy",
            {
                "fields": (
                    "parent",
                )
            },
        ),
        (
            "Media",
            {
                "fields": (
                    "image",
                )
            },
        ),
        (
            "Settings",
            {
                "fields": (
                    "is_active",
                    "display_order",
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
    ordering = ["display_order", "name"]
