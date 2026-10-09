import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.adventures.models import Adventure

from .forms import BookingRequestForm
from .models import BookingRequest

SIGNING_SALT = "adventure-booking-request"


@login_required
@require_http_methods(["GET", "POST"])
def create(request, slug):
    adventure = get_object_or_404(Adventure.objects.select_related("region"), slug=slug, is_active=True)
    initial = {
        "contact_name": request.user.get_full_name() or request.user.username,
        "email": request.user.email,
        "travellers": 1,
        "request_key": signing.dumps({"user": request.user.pk, "adventure": adventure.pk, "nonce": str(uuid.uuid4())}, salt=SIGNING_SALT),
    }
    form = BookingRequestForm(request.POST if request.method == "POST" else None, adventure=adventure, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            token = signing.loads(form.cleaned_data["request_key"], salt=SIGNING_SALT, max_age=86400)
            if token["user"] != request.user.pk or token["adventure"] != adventure.pk:
                raise signing.BadSignature
            submission_key = uuid.UUID(token["nonce"])
        except (signing.BadSignature, KeyError, ValueError, TypeError):
            form.add_error(None, "This form has expired or is invalid. Reload the page and try again.")
        else:
            defaults = {
                key: form.cleaned_data[key]
                for key in ("travel_date", "travellers", "contact_name", "email", "phone", "notes")
            }
            booking, created = BookingRequest.objects.get_or_create(
                submission_key=submission_key,
                defaults={**defaults, "user": request.user, "adventure": adventure,
                          "adventure_title": adventure.title, "duration_days": adventure.duration_days,
                          "unit_price": adventure.price, "currency": adventure.currency},
            )
            if created:
                messages.success(request, "Your booking request has been submitted. Track its status here or in My Bookings.")
            return redirect(booking)
    return render(request, "bookings/create.html", {"form": form, "adventure": adventure})


@login_required
def booking_list(request):
    bookings = BookingRequest.objects.filter(user=request.user).select_related("adventure", "adventure__region")
    status = request.GET.get("status", "")
    if status and status not in BookingRequest.Status.values:
        raise Http404("Unknown booking status")
    counts = dict(bookings.order_by().values("status").annotate(count=Count("pk")).values_list("status", "count"))
    total_count = sum(counts.values())
    if status:
        bookings = bookings.filter(status=status)
    return render(request, "bookings/list.html", {
        "page_obj": Paginator(bookings, 6).get_page(request.GET.get("page")),
        "selected_status": status, "total_count": total_count,
        "status_filters": [{"value": value, "label": label, "count": counts.get(value, 0)}
                           for value, label in BookingRequest.Status.choices],
        "query_string": f"status={status}" if status else "",
    })


@login_required
def detail(request, reference):
    booking = get_object_or_404(
        BookingRequest.objects.select_related("adventure", "adventure__region"),
        reference=reference, user=request.user,
    )
    return render(request, "bookings/detail.html", {"booking": booking})


@login_required
@require_http_methods(["GET", "POST"])
def cancel(request, reference):
    booking = get_object_or_404(BookingRequest, reference=reference, user=request.user)
    if not booking.can_cancel:
        messages.error(request, "This request can't be cancelled online. Contact our team if you need help.")
        return redirect(booking)
    if request.method == "POST":
        updated = BookingRequest.objects.filter(pk=booking.pk, status=booking.status).update(
            status=BookingRequest.Status.CANCELLED, updated_at=timezone.now()
        )
        if updated:
            messages.success(request, "Your booking request has been cancelled.")
        else:
            messages.error(request, "The status has changed. Please review your request and try again.")
        return redirect(booking)
    return render(request, "bookings/cancel.html", {"booking": booking})
