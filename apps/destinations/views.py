from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render

from apps.adventures.models import Adventure, Region


def region_list(request):
    """All destinations (regions) with their active adventure count."""
    regions = (
        Region.objects.annotate(
            adventure_count=Count(
                "adventures", filter=Q(adventures__is_active=True)
            )
        )
    )
    return render(
        request,
        "pages/destinations.html",
        {"regions": regions},
    )


def region_detail(request, slug):
    """A single destination plus the adventures that take place there."""
    region = get_object_or_404(Region, slug=slug)
    adventures = (
        Adventure.objects.filter(
            region=region,
            is_active=True,
        )
        .select_related("region")
        .prefetch_related("activities")
        .order_by("-rating", "-featured", "title", "pk")
    )
    page_obj = Paginator(adventures, 9).get_page(request.GET.get("page"))
    return render(
        request,
        "pages/destination_detail.html",
        {
            "region": region,
            "adventures": page_obj.object_list,
            "page_obj": page_obj,
            "adventure_count": page_obj.paginator.count,
        },
    )
