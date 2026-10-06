from django.contrib import admin
from django.utils import timezone

from .models import BookingRequest


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ("reference_code", "adventure_title", "contact_name", "travel_date", "travellers", "status", "display_total")
    list_filter = ("status", "travel_date")
    search_fields = ("reference", "contact_name", "email", "adventure_title")
    list_select_related = ("user", "adventure")
    date_hierarchy = "travel_date"
    readonly_fields = (
        "reference", "submission_key", "user", "adventure", "adventure_title", "duration_days",
        "travel_date", "travellers", "unit_price", "currency", "contact_name", "email", "phone",
        "notes", "display_total", "created_at", "updated_at",
    )
    actions = ("confirm_requests", "decline_requests")

    def has_add_permission(self, request):
        return False

    @admin.action(description="Confirm selected pending requests")
    def confirm_requests(self, request, queryset):
        count = queryset.filter(status=BookingRequest.Status.PENDING, travel_date__gt=timezone.localdate()).update(
            status=BookingRequest.Status.CONFIRMED, updated_at=timezone.now()
        )
        self.message_user(request, f"Confirmed {count} pending requests with future departure dates.")

    @admin.action(description="Decline selected pending requests")
    def decline_requests(self, request, queryset):
        count = queryset.filter(status=BookingRequest.Status.PENDING).update(
            status=BookingRequest.Status.DECLINED, updated_at=timezone.now()
        )
        self.message_user(request, f"Declined {count} pending requests.")
