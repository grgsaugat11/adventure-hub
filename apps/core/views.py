from django.shortcuts import render

from apps.adventures.models import Adventure

# Create your views here.
def home(request):
    featured_adventures = (
        Adventure.objects.filter(is_active=True, featured=True)
        .select_related("region")
        .order_by("-rating")
    )[:6]
    return render(
        request,
        "core/home.html",
        {"featured_adventures": featured_adventures},
    )