from django.contrib import admin
from .models import Activity, Adventure, Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "ordering")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("ordering", "name")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Adventure)
class AdventureAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "region",
        "difficulty",
        "duration_days",
        "price",
        "rating",
        "featured",
        "is_active",
    )
    list_filter = ("difficulty", "region", "featured", "is_active", "activities")
    search_fields = ("title", "short_description", "region__name")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("featured", "is_active")
    autocomplete_fields = ("region",)
    filter_horizontal = ("activities",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    fieldsets = (
        (
            "Basics",
            {"fields": ("title", "slug", "short_description", "overview", "image", "image_alt")},
        ),
        (
            "Categorization",
            {"fields": ("region", "activities", "difficulty")},
        ),
        (
            "Pricing & Capacity",
            {"fields": ("price", "currency", "duration_days", "max_group_size")},
        ),
        (
            "Social Proof",
            {"fields": ("rating", "review_count")},
        ),
        (
            "Publishing",
            {"fields": ("featured", "is_active", "created_at", "updated_at")},
        ),
    )