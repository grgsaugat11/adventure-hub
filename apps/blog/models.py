import math

from django.db import models
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True, published_at__lte=timezone.now())


class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    excerpt = models.CharField(max_length=300)
    body = models.TextField(help_text="Plain text. Separate paragraphs with a blank line.")
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="posts"
    )
    author = models.CharField(max_length=120, default="Adventure Nepal Team")
    image = models.ImageField(upload_to="blog/", blank=True)
    image_alt = models.CharField(max_length=255, blank=True)
    featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ("-published_at", "-pk")
        indexes = [models.Index(fields=("is_published", "published_at"))]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:detail", kwargs={"slug": self.slug})

    @property
    def reading_minutes(self):
        return max(1, math.ceil(len(self.body.split()) / 200))

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        covers = {
            "adventure-tips": "village.jpg",
            "destination-guide": "paragliding.jpg",
            "culture": "temple.jpg",
        }
        return static("images/blog/" + covers.get(self.category.slug, "village.jpg"))
