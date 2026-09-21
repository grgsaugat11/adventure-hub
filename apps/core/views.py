from django.db.models import Count, Q
from django.shortcuts import render

from apps.adventures.models import Adventure, Region

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

    return render(
        request,
        "core/home.html",
        {
            "featured_adventures": featured_adventures,
            "highlight_destinations": highlight_destinations,
        },
    )