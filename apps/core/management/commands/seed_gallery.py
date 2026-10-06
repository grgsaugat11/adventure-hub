from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.core.models import GalleryPhoto


PHOTOS = (
    ("Everest Horizons", "mountains", "images/everest.jpg", "Snow-covered peaks in the Everest region"),
    ("In the Annapurna Valley", "mountains", "images/annapurna.jpg", "Traveller looking across the Annapurna mountain valley"),
    ("The Landscapes of Mustang", "mountains", "images/popular/uppermustang.jpg", "Mountain landscape in Upper Mustang"),
    ("Lakeside Days", "lakes", "images/popular/lakeside.jpg", "Lake and mountain views around Pokhara"),
    ("Above Pokhara", "lakes", "images/blog/paragliding.jpg", "Paragliders above Pokhara with a lake in the distance"),
    ("A Living Heritage", "culture", "images/blog/temple.jpg", "Traditional temples in Nepal"),
    ("Life in the Mountains", "culture", "images/blog/village.jpg", "Himalayan village surrounded by mountains"),
    ("Into Chitwan", "wildlife", "images/chitwan.jpg", "Landscape of Chitwan National Park"),
)


class Command(BaseCommand):
    help = "Add starter gallery photos using existing images, preserving any edits."

    @transaction.atomic
    def handle(self, *args, **options):
        count = 0
        for index, (title, category, image, alt) in enumerate(PHOTOS):
            _, created = GalleryPhoto.objects.get_or_create(slug=slugify(title), defaults={
                "title": title, "category": category, "static_image": image,
                "image_alt": alt, "ordering": index,
            })
            count += created
        self.stdout.write(self.style.SUCCESS(f"Created {count} gallery photos."))
