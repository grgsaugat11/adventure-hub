from django.test import TestCase
from django.urls import reverse

from .models import Activity, Adventure, Region


class AdventureCatalogBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.everest = Region.objects.create(name="Everest Region", slug="everest")
        cls.annapurna = Region.objects.create(name="Annapurna Region", slug="annapurna")

        cls.trekking = Activity.objects.create(name="Trekking", slug="trekking")
        cls.safari = Activity.objects.create(name="Jungle Safari", slug="jungle-safari")

        cls.ebc = Adventure.objects.create(
            title="Everest Base Camp Trek",
            slug="everest-base-camp-trek",
            short_description="World's most iconic trek",
            overview="Long overview text about the Khumbu.",
            region=cls.everest,
            difficulty=Adventure.Difficulty.CHALLENGING,
            duration_days=12,
            price="1299.00",
            rating="4.9",
            review_count=214,
            featured=True,
            is_active=True,
        )
        cls.ebc.activities.set([cls.trekking])

        cls.safari_adventure = Adventure.objects.create(
            title="Chitwan Jungle Safari",
            slug="chitwan-jungle-safari",
            short_description="Safari in the Terai",
            overview="Safari overview.",
            region=Region.objects.get(slug="annapurna"),
            difficulty=Adventure.Difficulty.EASY,
            duration_days=3,
            price="399.00",
            rating="4.7",
            review_count=342,
            featured=False,
            is_active=True,
        )
        cls.safari_adventure.activities.set([cls.safari])

        cls.archived = Adventure.objects.create(
            title="Archived Nepal Tour",
            slug="archived-tour",
            short_description="Should never appear",
            overview="Hidden tour.",
            region=cls.annapurna,
            difficulty=Adventure.Difficulty.MODERATE,
            duration_days=5,
            price="500.00",
            rating="4.5",
            review_count=1,
            featured=False,
            is_active=False,
        )

    def get(self, url, **params):
        return self.client.get(url, params)


class AdventureListViewTests(AdventureCatalogBase):
    list_url = reverse("adventures:list")

    def test_lists_published_adventures_only(self):
        response = self.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Everest Base Camp Trek")
        self.assertNotContains(response, "Archived Nepal Tour")

    def test_region_filter(self):
        response = self.get(self.list_url, region="everest")
        self.assertContains(response, "Everest Base Camp Trek")
        self.assertNotContains(response, "Chitwan Jungle Safari")

    def test_difficulty_filter(self):
        response = self.get(self.list_url, difficulty="easy")
        self.assertContains(response, "Chitwan Jungle Safari")
        self.assertNotContains(response, "Everest Base Camp Trek")

    def test_activity_filter(self):
        response = self.get(self.list_url, activity="trekking")
        self.assertContains(response, "Everest Base Camp Trek")
        self.assertNotContains(response, "Chitwan Jungle Safari")

    def test_duration_bucket_filter(self):
        long_run = self.get(self.list_url, duration="long")
        self.assertContains(long_run, "Everest Base Camp Trek")
        self.assertNotContains(long_run, "Chitwan Jungle Safari")

        short_run = self.get(self.list_url, duration="short")
        self.assertContains(short_run, "Chitwan Jungle Safari")
        self.assertNotContains(short_run, "Everest Base Camp Trek")

    def test_price_bucket_filter(self):
        budget = self.get(self.list_url, price="budget")
        self.assertContains(budget, "Chitwan Jungle Safari")
        self.assertNotContains(budget, "Everest Base Camp Trek")

        premium = self.get(self.list_url, price="premium")
        self.assertContains(premium, "Everest Base Camp Trek")

    def test_search_by_keyword(self):
        response = self.get(self.list_url, q="khumbu")
        self.assertContains(response, "Everest Base Camp Trek")
        self.assertNotContains(response, "Chitwan Jungle Safari")

    def test_sort_without_filters(self):
        response = self.get(self.list_url, sort="price_high")
        content = response.content.decode()
        self.assertLess(content.index("Everest Base Camp Trek"), content.index("Chitwan Jungle Safari"))

    def test_combined_filters(self):
        response = self.get(self.list_url, region="annapurna", difficulty="moderate")
        # Archived adventure is excluded despite matching filters.
        self.assertNotContains(response, "Archived Nepal Tour")

    def test_empty_results_state(self):
        response = self.get(self.list_url, q="no-such-place-on-earth")
        self.assertContains(response, "No adventures matched your filters")

    def test_pagination_metadata_present(self):
        response = self.get(self.list_url)
        self.assertContains(response, "Showing 2")


class AdventureDetailViewTests(AdventureCatalogBase):
    def test_renders_active_adventure(self):
        response = self.client.get(reverse("adventures:detail", args=["everest-base-camp-trek"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Experience")

    def test_inactive_adventure_is_hidden(self):
        response = self.client.get(reverse("adventures:detail", args=["archived-tour"]))
        self.assertEqual(response.status_code, 404)

    def test_unknown_slug_returns_404(self):
        response = self.client.get(reverse("adventures:detail", args=["does-not-exist"]))
        self.assertEqual(response.status_code, 404)