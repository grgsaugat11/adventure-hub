from django.test import Client, TestCase, override_settings
from django.core.cache import cache
from unittest.mock import patch
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


@override_settings(SUBMISSION_RATE_LIMITS={})
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

    def test_gallery_pagination_preserves_category(self):
        for index in range(13):
            GalleryPhoto.objects.create(title=f"Mountain {index}", slug=f"mountain-{index}", category="mountains")
        GalleryPhoto.objects.create(title="Lake", slug="lake", category="lakes")
        response = self.client.get(reverse("core:gallery"), {"category": "mountains"})
        self.assertEqual(len(response.context["photos"]), 12)
        self.assertContains(response, "category=mountains&amp;page=2")
        response = self.client.get(reverse("core:gallery"), {"category": "mountains", "page": 2})
        self.assertEqual(len(response.context["photos"]), 1)
        self.assertEqual(response.context["page_obj"].paginator.count, 13)


@override_settings(SUBMISSION_RATE_LIMITS={"core:contact": (2, 60), "accounts:login": (2, 60)})
class SubmissionThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.data = {"name": "Traveller", "email": "traveller@example.com", "topic": "planning", "message": "Help me plan a journey."}

    @patch("apps.core.middleware.time.time", return_value=120)
    def test_throttle_prevents_extra_writes_and_returns_retry_after(self, clock):
        url = reverse("core:contact")
        self.assertEqual(self.client.post(url, self.data).status_code, 302)
        self.assertEqual(self.client.post(url, self.data).status_code, 302)
        response = self.client.post(url, self.data)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "60")
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(ContactMessage.objects.count(), 2)
        self.assertContains(response, "Please pause", status_code=429)

    @patch("apps.core.middleware.time.time", return_value=120)
    def test_limits_expire_and_ips_and_routes_are_independent(self, clock):
        url = reverse("core:contact")
        for _ in range(2):
            self.client.post(url, self.data)
        self.assertEqual(self.client.post(url, self.data).status_code, 429)
        self.assertEqual(self.client.post(url, self.data, REMOTE_ADDR="192.0.2.2").status_code, 302)
        self.assertEqual(self.client.post(reverse("accounts:login"), {}).status_code, 200)
        self.assertEqual(self.client.get(url).status_code, 200)
        clock.return_value = 180
        self.assertEqual(self.client.post(url, self.data).status_code, 302)

    def test_forwarded_ip_header_does_not_bypass_limits(self):
        for _ in range(2):
            self.client.post(reverse("core:contact"), self.data)
        response = self.client.post(reverse("core:contact"), self.data, HTTP_X_FORWARDED_FOR="192.0.2.3")
        self.assertEqual(response.status_code, 429)

    def test_csrf_rejection_still_prevents_storage(self):
        response = Client(enforce_csrf_checks=True).post(reverse("core:contact"), self.data)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(ContactMessage.objects.exists())


class ErrorPageTests(TestCase):
    @override_settings(DEBUG=False)
    def test_missing_page_uses_branded_error_template(self):
        response = self.client.get("/no-such-trail/")
        self.assertContains(response, "This trail doesn't lead anywhere", status_code=404)
        self.assertTemplateUsed(response, "404.html")

    def test_server_error_template_renders_without_request_context(self):
        from django.template.loader import render_to_string
        html = render_to_string("500.html")
        self.assertIn("A small detour", html)
        self.assertNotIn("Traceback", html)
