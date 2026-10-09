from decimal import Decimal
from io import StringIO
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Activity, Adventure, Region
from .filters import apply_price_filter, apply_sort, price_bucket_counts


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


class CatalogRegressionTests(AdventureCatalogBase):
    def test_price_buckets_are_disjoint_and_match_counts_and_labels(self):
        prices = ("499.99", "500.00", "500.01", "1200.00", "1200.01")
        expected = ("budget", "budget", "standard", "standard", "premium")
        records = []
        for index, price in enumerate(prices):
            records.append(Adventure.objects.create(title=f"Boundary {index}", slug=f"boundary-{index}", short_description="Boundary", overview="Boundary", region=self.everest, duration_days=1, price=price))
        queryset = Adventure.objects.filter(pk__in=[record.pk for record in records])
        self.assertEqual(price_bucket_counts(queryset.distinct()), {"budget": 2, "standard": 2, "premium": 1})
        for record, bucket in zip(records, expected):
            record.price = Decimal(record.price)
            self.assertEqual(record.price_bucket, bucket)
            for other in ("budget", "standard", "premium"):
                self.assertEqual(apply_price_filter(queryset, other).filter(pk=record.pk).exists(), bucket == other)

    def test_selected_facets_keep_other_options_available(self):
        for query, group, other in (({"difficulty": "easy"}, "difficulties", "challenging"), ({"duration": "short"}, "durations", "long"), ({"price": "budget"}, "prices", "premium")):
            with self.subTest(query=query):
                response = self.client.get(reverse("adventures:list"), query)
                counts = {option["key"]: option["count"] for option in response.context[group]}
                self.assertEqual(counts[other], 1)

    def test_activity_facet_counts_and_unassigned_adventures(self):
        self.ebc.activities.add(self.safari)
        Adventure.objects.create(title="Unassigned", slug="unassigned", short_description="Trip", overview="Trip", region=self.everest, duration_days=2, price=100)
        response = self.client.get(reverse("adventures:list"), {"activity": "trekking"})
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        counts = {option["name"]: option["count"] for option in response.context["activities"]}
        self.assertEqual(counts, {"Jungle Safari": 2, "Trekking": 1})
        response = self.client.get(reverse("adventures:list"))
        self.assertTrue(all(option["name"] for option in response.context["activities"]))

    def test_sort_has_unique_tiebreaker_and_price_keeps_cents(self):
        self.assertEqual(apply_sort(Adventure.objects.all(), "price_low").query.order_by, ("price", "pk"))
        self.safari_adventure.price = Decimal("125.50")
        self.assertEqual(self.safari_adventure.display_price, "USD 125.50")

    def test_facet_counts_combine_records_with_different_titles_and_ratings(self):
        Adventure.objects.create(title="Another short trip", slug="another-short-trip", short_description="Trip", overview="Trip", region=self.annapurna, difficulty="easy", duration_days=2, price=125, rating="4.5")
        response = self.client.get(reverse("adventures:list"))
        for group, key in (("difficulties", "easy"), ("durations", "short"), ("prices", "budget")):
            counts = {item["key"]: item["count"] for item in response.context[group]}
            self.assertEqual(counts[key], 2)
            self.assertEqual(sum(counts.values()), 3)


class SeedAdventureTests(TestCase):
    def test_seed_preserves_edits_archiving_images_and_activities(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            call_command("seed_adventures", stdout=StringIO())
            adventure = Adventure.objects.get(slug="everest-base-camp-trek")
            adventure.title = "An editor's title"
            adventure.price = Decimal("1234.56")
            adventure.is_active = False
            adventure.image = "adventures/custom.jpg"
            adventure.save()
            adventure.activities.clear()
            region = adventure.region
            region.description = "An editor's region"
            region.save()
            activity = Activity.objects.get(slug="trekking")
            activity.name = "An editor's activity"
            activity.save()
            call_command("seed_adventures", stdout=StringIO())
            adventure.refresh_from_db()
            region.refresh_from_db()
            self.assertEqual(Adventure.objects.count(), 12)
            self.assertEqual(adventure.title, "An editor's title")
            self.assertEqual(adventure.price, Decimal("1234.56"))
            self.assertFalse(adventure.is_active)
            self.assertEqual(adventure.image.name, "adventures/custom.jpg")
            self.assertEqual(adventure.activities.count(), 0)
            self.assertEqual(region.description, "An editor's region")
            activity.refresh_from_db()
            self.assertEqual(activity.name, "An editor's activity")
