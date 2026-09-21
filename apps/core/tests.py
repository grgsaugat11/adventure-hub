from django.test import TestCase
from django.urls import reverse

from apps.adventures.models import Activity, Adventure, Region


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