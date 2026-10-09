from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.utils.text import slugify

# ===========================================
# DOMAIN CONSTANTS
# ===========================================

DURATION_BUCKETS = (
    ("short", "Short (1 - 4 days)"),
    ("medium", "Medium (5 - 9 days)"),
    ("long", "Long (10+ days)"),
)

PRICE_BUCKETS = (
    ("budget", "$500 or less"),
    ("standard", "Over $500 to $1,200"),
    ("premium", "Over $1,200"),
)


def duration_bucket_for(days: int) -> str:
    """Map a duration in days to its filter bucket."""
    if days <= 4:
        return "short"
    if days <= 9:
        return "medium"
    return "long"


def price_bucket_for(price) -> str:
    """Map a price to its filter bucket."""
    price = Decimal(str(price))
    if price <= 500:
        return "budget"
    if price <= 1200:
        return "standard"
    return "premium"


# ===========================================
# MODELS
# ===========================================


class Region(models.Model):
    """A geographic region of Nepal where adventures take place."""

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.CharField(max_length=255, blank=True)
    ordering = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="destinations/", blank=True)
    image_alt = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("ordering", "name")
        verbose_name = "Region"
        verbose_name_plural = "Regions"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Activity(models.Model):
    """A type of adventure activity (e.g. Trekking, Rafting, Safari)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Activity"
        verbose_name_plural = "Activities"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Adventure(models.Model):
    """A bookable adventure experience."""

    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MODERATE = "moderate", "Moderate"
        CHALLENGING = "challenging", "Challenging"
        DIFFICULT = "difficult", "Difficult"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    short_description = models.CharField(max_length=255)
    overview = models.TextField()

    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name="adventures",
        db_index=True,
    )
    activities = models.ManyToManyField(
        Activity,
        related_name="adventures",
        blank=True,
    )
    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.MODERATE,
        db_index=True,
    )
    duration_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    max_group_size = models.PositiveIntegerField(default=12)

    image = models.ImageField(upload_to="adventures/", blank=True)
    image_alt = models.CharField(max_length=255, blank=True)

    rating = models.DecimalField(max_digits=3, decimal_places=1, default=5.0)
    review_count = models.PositiveIntegerField(default=0)

    featured = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-featured", "-rating", "title")
        verbose_name = "Adventure"
        verbose_name_plural = "Adventures"
        indexes = [
            models.Index(fields=("is_active", "featured", "difficulty")),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("adventures:detail", kwargs={"slug": self.slug})

    @property
    def duration_bucket(self) -> str:
        return duration_bucket_for(self.duration_days)

    @property
    def price_bucket(self) -> str:
        return price_bucket_for(self.price)

    @property
    def display_price(self) -> str:
        return f"{self.currency} {self.price:,.2f}"
