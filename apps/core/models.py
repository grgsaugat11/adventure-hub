from django.db import models
from django.templatetags.static import static
from django.utils.text import slugify


class ContactMessage(models.Model):
    class Topic(models.TextChoices):
        PLANNING = "planning", "Planning an adventure"
        BOOKING = "booking", "An existing booking request"
        GENERAL = "general", "Something else"

    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_PROGRESS = "in_progress", "In Progress"
        CLOSED = "closed", "Closed"

    name = models.CharField(max_length=150)
    email = models.EmailField()
    topic = models.CharField(max_length=20, choices=Topic.choices)
    message = models.TextField(max_length=4000)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-pk")

    def __str__(self):
        return f"{self.name} — {self.get_topic_display()}"


GALLERY_COVERS = (
    ("images/everest.jpg", "Everest"),
    ("images/annapurna.jpg", "Annapurna"),
    ("images/popular/uppermustang.jpg", "Mustang"),
    ("images/popular/lakeside.jpg", "Pokhara Lake"),
    ("images/blog/paragliding.jpg", "Paragliding"),
    ("images/blog/temple.jpg", "Temple"),
    ("images/blog/village.jpg", "Himalayan Village"),
    ("images/chitwan.jpg", "Chitwan"),
)


class GalleryPhoto(models.Model):
    class Category(models.TextChoices):
        MOUNTAINS = "mountains", "Mountains"
        LAKES = "lakes", "Lakes & Adventure"
        CULTURE = "culture", "Culture"
        WILDLIFE = "wildlife", "Wildlife"

    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True)
    caption = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    image = models.ImageField(upload_to="gallery/", blank=True)
    static_image = models.CharField(max_length=150, choices=GALLERY_COVERS, default="images/everest.jpg", help_text="Used when no image is uploaded.")
    image_alt = models.CharField(max_length=255, blank=True)
    ordering = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("ordering", "title", "pk")
        verbose_name_plural = "Gallery photos"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def image_url(self):
        return self.image.url if self.image else static(self.static_image)
