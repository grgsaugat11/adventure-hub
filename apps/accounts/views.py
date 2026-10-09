from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from apps.bookings.models import BookingRequest

from .forms import ProfileForm, SignupForm


def signup(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")
    next_url = request.POST.get("next") or request.GET.get("next", "")
    form = SignupForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return redirect(next_url)
        return redirect("accounts:profile")
    return render(request, "accounts/signup.html", {"form": form, "next": next_url})


@login_required
def profile(request):
    # Keep the identity header tied to saved details on invalid form submissions.
    name = request.user.get_full_name().strip() or request.user.username
    name_parts = name.split()
    identity = {
        "profile_name": name,
        "profile_initials": (name_parts[0][0] + name_parts[-1][0] if len(name_parts) > 1 else name[:2]).upper(),
        "profile_email": request.user.email,
        "greeting_name": request.user.first_name or request.user.username,
    }
    form = ProfileForm(request.POST if request.method == "POST" else None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your account details have been updated.")
        return redirect("accounts:profile")
    today = timezone.localdate()
    bookings = BookingRequest.objects.filter(user=request.user)
    upcoming = Q(status=BookingRequest.Status.CONFIRMED, travel_date__gte=today)
    booking_stats = bookings.aggregate(
        total=Count("pk"),
        upcoming=Count("pk", filter=upcoming),
        pending=Count("pk", filter=Q(status=BookingRequest.Status.PENDING)),
    )
    next_trip = (
        bookings.filter(upcoming)
        .select_related("adventure", "adventure__region")
        .order_by("travel_date", "pk")
        .first()
    )
    return render(request, "accounts/profile.html", {
        "form": form, "booking_stats": booking_stats, "next_trip": next_trip, **identity,
    })
