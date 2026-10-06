from django.contrib import admin

from .models import Category, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "is_published", "featured", "published_at")
    list_filter = ("is_published", "featured", "category")
    search_fields = ("title", "excerpt", "body", "author")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
    list_select_related = ("category",)
    readonly_fields = ("created_at", "updated_at")
