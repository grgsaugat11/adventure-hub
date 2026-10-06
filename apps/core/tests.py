from django.test import TestCase
from django.urls import reverse
from django.core.management import call_command
from io import StringIO

from apps.adventures.models import Activity, Adventure, Region
from apps.blog.models import Category, Post

from .models import ContactMessage, GalleryPhoto


class HomePageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.everest = Region.objects.create(
            name="Everest Region", slug="everest", ordering=1
        )

        cls.trekking = Activity.objects.create(name="Trekking", slug="trekking")

        cls.ebc = Adventure.objects.create(
            title="Everest Base Camp Trek",
            slug="everest-base-camp-trek",
            short_description="World's most iconic trek",
            overview="A long overview about the Khumbu.",
            region=cls.everest,
            difficulty=Adventure.Difficulty.CHALLENGING,
            duration_days=12,
            price="1299.00",
            rating="4.9",
            featured=True,
            is_active=True,
        )
        cls.ebc.activities.set([cls.trekking])

    def test_home_renders(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)

    def test_featured_adventures_carousel_present(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "data-carousel")
        self.assertContains(response, "Everest Base Camp Trek")

    def test_homepage_destinations_section_present(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "Everest Region")
        self.assertContains(response, reverse("destinations:detail", args=["everest"]))


class SupportPageTests(TestCase):
    def test_contact_message_is_stored_and_refresh_does_not_resubmit(self):
        response = self.client.post(reverse("core:contact"), {
            "name": "A Traveller", "email": "traveller@example.com", "topic": "planning",
            "message": "I'd like to plan a trip to Nepal.", "status": "closed",
        }, follow=True)
        self.assertContains(response, "Your message has reached our team")
        message = ContactMessage.objects.get()
        self.assertEqual(message.status, ContactMessage.Status.NEW)
        self.client.get(reverse("core:contact"))
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_invalid_contact_is_not_stored(self):
        response = self.client.post(reverse("core:contact"), {"name": "Visitor", "email": "invalid", "topic": "not-a-topic", "message": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_gallery_filters_hide_inactive_images(self):
        mountain = GalleryPhoto.objects.create(title="Mountain", slug="mountain", category="mountains")
        GalleryPhoto.objects.create(title="Lake", slug="lake", category="lakes")
        GalleryPhoto.objects.create(title="Hidden", slug="hidden", category="mountains", is_active=False)
        response = self.client.get(reverse("core:gallery"), {"category": "mountains"})
        self.assertContains(response, mountain.title)
        self.assertEqual(list(response.context["photos"]), [mountain])
        self.assertEqual(self.client.get(reverse("core:gallery"), {"category": "unknown"}).status_code, 404)

    def test_gallery_seed_preserves_edits(self):
        call_command("seed_gallery", stdout=StringIO())
        self.assertEqual(GalleryPhoto.objects.count(), 8)
        photo = GalleryPhoto.objects.first()
        photo.caption = "An edited caption"
        photo.save()
        call_command("seed_gallery", stdout=StringIO())
        photo.refresh_from_db()
        self.assertEqual(photo.caption, "An edited caption")
        self.assertEqual(GalleryPhoto.objects.count(), 8)

    def test_support_pages_and_navigation_have_no_placeholder_links(self):
        for name in ("home", "about", "contact", "gallery", "privacy"):
            response = self.client.get(reverse(f"core:{name}"))
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, 'href="#"')

    def test_home_story_links_fall_back_when_story_is_not_public(self):
        category = Category.objects.create(name="Tips", slug="tips")
        post = Post.objects.create(title="Everest Tips", slug="everest-base-camp-trekking-tips", excerpt="An excerpt", body="Story body", category=category, is_published=True)
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.context["home_story_links"]["everest"], post.get_absolute_url())
        Post.objects.filter(pk=post.pk).update(is_published=False)
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.context["home_story_links"]["everest"], reverse("blog:list"))
