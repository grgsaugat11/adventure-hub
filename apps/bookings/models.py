import uuid

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class BookingRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Under Review"
        CONFIRMED = "confirmed", "Confirmed"
        DECLINED = "declined", "Declined"
        CANCELLED = "cancelled", "Cancelled"

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    submission_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="booking_requests")
    adventure = models.ForeignKey("adventures.Adventure", on_delete=models.PROTECT, related_name="booking_requests")
    adventure_title = models.CharField(max_length=200)
    duration_days = models.PositiveIntegerField()
    travel_date = models.DateField()
    travellers = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default="USD")
    contact_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, validators=[RegexValidator(
        r"^\+?[0-9][0-9\s().-]{6,24}$", "Enter a valid phone number, including your country code."
    )])
    notes = models.TextField(blank=True, max_length=2000)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    team_notes = models.TextField(blank=True, help_text="Internal notes; not shown to travellers.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        indexes = [models.Index(fields=("user", "status"))]
        constraints = [
            models.CheckConstraint(condition=models.Q(travellers__gte=1), name="booking_travellers_positive"),
            models.CheckConstraint(condition=models.Q(unit_price__gte=0), name="booking_price_nonnegative"),
        ]

    def __str__(self):
        return f"{self.reference_code} — {self.adventure_title}"

    def get_absolute_url(self):
        return reverse("bookings:detail", kwargs={"reference": self.reference})

    @property
    def reference_code(self):
        return "AN-" + str(self.reference).split("-")[0].upper()

    @property
    def total_price(self):
        return self.unit_price * self.travellers

    @property
    def display_total(self):
        return f"{self.currency} {self.total_price:,.2f}"

    @property
    def can_cancel(self):
        days_remaining = (self.travel_date - timezone.localdate()).days
        return (
            self.status == self.Status.PENDING and days_remaining > 0
        ) or (
            self.status == self.Status.CONFIRMED and days_remaining >= 15
        )

    @property
    def status_description(self):
        return {
            self.Status.PENDING: "Your request is with our team. Your preferred date and arrangements are not confirmed yet.",
            self.Status.CONFIRMED: "Our team has confirmed your request. Please contact us to discuss final arrangements and payment.",
            self.Status.DECLINED: "We couldn't confirm this request. Contact our team to discuss another date or adventure.",
            self.Status.CANCELLED: "This booking request has been cancelled. You can browse adventures and submit a new request whenever you're ready.",
        }[self.status]
