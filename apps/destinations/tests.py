from django.test import TestCase
from django.urls import reverse

from apps.adventures.models import Activity, Adventure, Region


class DestinationPageBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.everest = Region.objects.create(
            name="Everest Region",
            slug="everest",
            description="Sagarmatha and Khumbu Himalaya",
        )
        cls.chitwan = Region.objects.create(
            name="Chitwan & Terai",
            slug="chitwan-terai",
            description="Jungle parks of the lowlands",
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

        cls.archived = Adventure.objects.create(
            title="Archived Chitwan Tour",
            slug="archived-chitwan-tour",
            short_description="Should never appear",
            overview="Hidden tour.",
            region=cls.chitwan,
            difficulty=Adventure.Difficulty.EASY,
            duration_days=3,
            price="399.00",
            rating="4.5",
            is_active=False,
        )


class DestinationListPageTests(DestinationPageBase):
    def test_lists_all_regions_with_counts(self):
        response = self.client.get(reverse("destinations:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Everest Region")
        self.assertContains(response, "Chitwan &amp; Terai")

    def test_count_ignores_inactive_adventures(self):
        response = self.client.get(reverse("destinations:list"))
        regions = response.context["regions"]
        self.assertEqual(regions.get(slug="everest").adventure_count, 1)
        self.assertEqual(regions.get(slug="chitwan-terai").adventure_count, 0)

    def test_region_cards_link_to_detail(self):
        response = self.client.get(reverse("destinations:list"))
        self.assertContains(response, reverse("destinations:detail", args=["everest"]))


class DestinationDetailPageTests(DestinationPageBase):
    def test_renders_region_and_active_adventures(self):
        response = self.client.get(reverse("destinations:detail", args=["everest"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Everest Base Camp Trek")
        self.assertContains(response, "Adventures in")

    def test_inactive_adventures_are_hidden(self):
        response = self.client.get(reverse("destinations:detail", args=["chitwan-terai"]))
        self.assertContains(response, "No adventures in this destination yet")
        self.assertNotContains(response, "Archived Chitwan Tour")

    def test_unknown_slug_returns_404(self):
        response = self.client.get(reverse("destinations:detail", args=["does-not-exist"]))
        self.assertEqual(response.status_code, 404)

    def test_destination_adventures_are_paginated_with_total_count(self):
        for index in range(10):
            Adventure.objects.create(title=f"Trip {index}", slug=f"trip-{index}", short_description="Trip", overview="Trip", region=self.everest, duration_days=2, price=100)
        response = self.client.get(reverse("destinations:detail", args=["everest"]))
        self.assertEqual(len(response.context["adventures"]), 9)
        self.assertEqual(response.context["adventure_count"], 11)
        response = self.client.get(reverse("destinations:detail", args=["everest"]), {"page": 2})
        self.assertEqual(len(response.context["adventures"]), 2)
