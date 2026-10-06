from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Post


class BlogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tips = Category.objects.create(name="Adventure Tips", slug="adventure-tips")
        cls.culture = Category.objects.create(name="Culture", slug="culture")
        cls.now = timezone.now()
        cls.published = Post.objects.create(
            title="A guide to the Everest trail",
            slug="everest-trail",
            excerpt="Get ready for your journey.",
            body="Walk at your own pace.\n\nEnjoy the mountain views.",
            category=cls.tips,
            is_published=True,
            featured=True,
            published_at=cls.now - timedelta(days=1),
        )
        cls.other = Post.objects.create(
            title="Valley traditions",
            slug="valley-traditions",
            excerpt="Stories from local communities.",
            body="A journey through temples in the Kathmandu valley.",
            category=cls.culture,
            is_published=True,
            published_at=cls.now - timedelta(days=2),
        )
        cls.draft = Post.objects.create(
            title="Unpublished trail notes",
            slug="draft-notes",
            excerpt="Draft excerpt",
            body="Draft content",
            category=cls.tips,
            featured=True,
        )
        cls.scheduled = Post.objects.create(
            title="Tomorrow's expedition",
            slug="scheduled-expedition",
            excerpt="Future story",
            body="Future content",
            category=cls.tips,
            is_published=True,
            featured=True,
            published_at=cls.now + timedelta(days=1),
        )

    def test_listing_only_shows_published_stories(self):
        response = self.client.get(reverse("blog:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published.title)
        self.assertContains(response, self.other.title)
        self.assertNotContains(response, self.draft.title)
        self.assertNotContains(response, self.scheduled.title)
        counts = {category.slug: category.post_count for category in response.context["categories"]}
        self.assertEqual(counts, {"adventure-tips": 1, "culture": 1})

    def test_drafts_and_scheduled_stories_are_not_accessible(self):
        for slug in (self.draft.slug, self.scheduled.slug, "missing-story"):
            with self.subTest(slug=slug):
                response = self.client.get(reverse("blog:detail", args=[slug]))
                self.assertEqual(response.status_code, 404)

    def test_search_matches_body_and_combines_with_category(self):
        response = self.client.get(reverse("blog:list"), {"q": "temples"})
        self.assertContains(response, self.other.title)
        self.assertNotContains(response, self.published.title)
        response = self.client.get(reverse("blog:list"), {
            "q": "temples", "category": self.tips.slug,
        })
        self.assertContains(response, "No stories found")
        self.assertEqual(response.context["page_obj"].paginator.count, 0)

    def test_category_filter(self):
        response = self.client.get(reverse("blog:list"), {"category": self.tips.slug})
        self.assertContains(response, self.published.title)
        self.assertNotContains(response, self.other.title)
        self.assertEqual(response.context["selected_category"], self.tips)

    def test_unknown_category_returns_404(self):
        response = self.client.get(reverse("blog:list"), {"category": "missing"})
        self.assertEqual(response.status_code, 404)

    def test_pagination_keeps_search_and_category(self):
        for index in range(7):
            Post.objects.create(
                title=f"Trail story {index}",
                slug=f"trail-story-{index}",
                excerpt="Trail inspiration",
                body="A local journey.",
                category=self.tips,
                is_published=True,
                published_at=self.now - timedelta(days=3),
            )
        response = self.client.get(reverse("blog:list"), {
            "q": "trail", "category": self.tips.slug,
        })
        self.assertEqual(len(response.context["page_obj"]), 6)
        self.assertContains(response, "q=trail&amp;category=adventure-tips&amp;page=2")
        response = self.client.get(reverse("blog:list"), {
            "q": "trail", "category": self.tips.slug, "page": "2",
        })
        self.assertEqual(len(response.context["page_obj"]), 2)
        response = self.client.get(reverse("blog:list"), {"page": "invalid"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 1)

    def test_detail_formats_plain_text_and_escapes_html(self):
        self.published.body = "First paragraph.\n\n<script>alert('hello')</script>"
        self.published.save()
        response = self.client.get(self.published.get_absolute_url())
        self.assertContains(response, "<p>First paragraph.</p>", html=True)
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>alert(")

    def test_related_stories_exclude_current_draft_and_scheduled_posts(self):
        response = self.client.get(self.published.get_absolute_url())
        self.assertEqual(list(response.context["related_posts"]), [])
        self.other.category = self.tips
        self.other.save()
        response = self.client.get(self.published.get_absolute_url())
        self.assertEqual(list(response.context["related_posts"]), [self.other])

    def test_empty_listing_has_explore_link(self):
        Post.objects.all().delete()
        response = self.client.get(reverse("blog:list"))
        self.assertContains(response, "The next chapter is on its way")
        self.assertContains(response, reverse("adventures:list"))


class SeedBlogTests(TestCase):
    def test_seed_is_repeatable_and_preserves_edits(self):
        call_command("seed_blog", stdout=StringIO())
        self.assertEqual(Post.objects.published().count(), 3)
        post = Post.objects.get(slug="everest-base-camp-trekking-tips")
        post.title = "An editor's updated title"
        post.save()
        call_command("seed_blog", stdout=StringIO())
        self.assertEqual(Post.objects.count(), 3)
        self.assertEqual(Category.objects.count(), 3)
        post.refresh_from_db()
        self.assertEqual(post.title, "An editor's updated title")
