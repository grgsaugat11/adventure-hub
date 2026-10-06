from django.contrib import messages
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.adventures.models import Adventure, Region
from apps.blog.models import Post

from .forms import ContactForm
from .models import GalleryPhoto

# Destinations highlighted on the homepage, in the editorial order of the
# featured mosaic (large card first, wide card last).
HOMEPAGE_DESTINATION_SLUGS = (
    "everest",
    "pokhara-gandaki",
    "chitwan-terai",
    "mustang",
)

# Create your views here.
def home(request):
    featured_adventures = (
        Adventure.objects.filter(is_active=True, featured=True)
        .select_related("region")
        .order_by("-rating")
    )[:6]

    regions = {
        region.slug: region
        for region in Region.objects.filter(
            slug__in=HOMEPAGE_DESTINATION_SLUGS
        ).annotate(
            adventure_count=Count(
                "adventures", filter=Q(adventures__is_active=True)
            )
        )
    }
    highlight_destinations = [
        regions[slug] for slug in HOMEPAGE_DESTINATION_SLUGS if slug in regions
    ]

    story_slugs = {
        "everest": "everest-base-camp-trekking-tips",
        "pokhara": "pokhara-first-stop-nepal",
        "culture": "nepal-beyond-the-mountains",
    }
    stories = {post.slug: post for post in Post.objects.published().filter(slug__in=story_slugs.values())}
    home_story_links = {
        key: stories[slug].get_absolute_url() if slug in stories else reverse("blog:list")
        for key, slug in story_slugs.items()
    }

    return render(
        request,
        "core/home.html",
        {
            "featured_adventures": featured_adventures,
            "highlight_destinations": highlight_destinations,
            "home_story_links": home_story_links,
        },
    )


def about(request):
    return render(request, "pages/about.html")


@require_http_methods(["GET", "POST"])
def contact(request):
    initial = {}
    if request.user.is_authenticated:
        initial = {"name": request.user.get_full_name() or request.user.username, "email": request.user.email}
    form = ContactForm(request.POST if request.method == "POST" else None, initial=initial)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Thanks for getting in touch. Your message has reached our team, and we'll reply to the email you provided.")
        return redirect("core:contact")
    return render(request, "pages/contact.html", {"form": form})


def gallery(request):
    category = request.GET.get("category", "")
    if category and category not in GalleryPhoto.Category.values:
        raise Http404("Unknown gallery category")
    photos = GalleryPhoto.objects.filter(is_active=True)
    if category:
        photos = photos.filter(category=category)
    return render(request, "pages/gallery.html", {
        "photos": photos, "categories": GalleryPhoto.Category.choices, "selected_category": category,
    })


def privacy(request):
    return render(request, "pages/privacy.html")
