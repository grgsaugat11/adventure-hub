from django.contrib import admin

from .models import ContactMessage, GalleryPhoto


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "topic", "status", "created_at")
    list_filter = ("status", "topic")
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email", "topic", "message", "created_at")

    def has_add_permission(self, request):
        return False


@admin.register(GalleryPhoto)
class GalleryPhotoAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "ordering", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("title", "caption")
    prepopulated_fields = {"slug": ("title",)}
