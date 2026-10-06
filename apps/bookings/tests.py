from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.adventures.models import Adventure, Region

from .models import BookingRequest

User = get_user_model()


class BookingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("bookingtraveller", "traveller@example.com", "Forest-River!2026")
        cls.other = User.objects.create_user("othertraveller", "other@example.com", "Forest-River!2026")
        cls.staff = User.objects.create_superuser("bookingadmin", "admin@example.com", "Forest-River!2026")
        region = Region.objects.create(name="Booking Region", slug="booking-region")
        cls.adventure = Adventure.objects.create(
            title="River Adventure", slug="river-adventure", short_description="Explore the river.",
            overview="A journey by the river.", region=region, duration_days=3,
            price="125.50", max_group_size=8, is_active=True,
        )

    def setUp(self):
        self.client.force_login(self.user)
        self.create_url = reverse("bookings:create", args=[self.adventure.slug])

    def payload(self, **changes):
        response = self.client.get(self.create_url)
        return {"request_key": response.context["form"].initial["request_key"],
                "travel_date": (timezone.localdate() + timedelta(days=30)).isoformat(),
                "travellers": 2, "contact_name": "A Traveller", "email": "traveller@example.com",
                "phone": "+977 9812345678", "notes": "A riverside stay, please.", **changes}

    def make_booking(self, **changes):
        return BookingRequest.objects.create(
            user=self.user, adventure=self.adventure, adventure_title=self.adventure.title,
            duration_days=3, travel_date=changes.pop("travel_date", timezone.localdate() + timedelta(days=30)),
            travellers=2, unit_price="125.50", currency="USD", contact_name="A Traveller",
            email="traveller@example.com", phone="+9779812345678", **changes,
        )

    def test_anonymous_booking_redirect_preserves_destination(self):
        self.client.logout()
        response = self.client.get(self.create_url)
        self.assertRedirects(response, reverse("accounts:login") + "?next=" + self.create_url)

    def test_request_saves_server_side_price_owner_and_pending_status(self):
        data = self.payload(unit_price="0", status="confirmed", user=self.other.pk, currency="NPR")
        response = self.client.post(self.create_url, data)
        booking = BookingRequest.objects.get()
        self.assertRedirects(response, booking.get_absolute_url())
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.unit_price, Decimal("125.50"))
        self.assertEqual(booking.currency, "USD")
        self.assertEqual(booking.total_price, Decimal("251.00"))
        self.assertEqual(booking.status, BookingRequest.Status.PENDING)

    def test_double_submit_does_not_duplicate_request(self):
        data = self.payload()
        first = self.client.post(self.create_url, data)
        second = self.client.post(self.create_url, data)
        self.assertEqual(first.url, second.url)
        self.assertEqual(BookingRequest.objects.count(), 1)

    def test_price_and_title_snapshot_survive_catalogue_edits(self):
        self.client.post(self.create_url, self.payload())
        booking = BookingRequest.objects.get()
        Adventure.objects.filter(pk=self.adventure.pk).update(price="999.00", title="Updated title")
        booking.refresh_from_db()
        self.assertEqual(booking.display_total, "USD 251.00")
        self.assertEqual(booking.adventure_title, "River Adventure")

    def test_date_and_group_limits_are_validated(self):
        for changes in (
            {"travel_date": timezone.localdate().isoformat()},
            {"travel_date": (timezone.localdate() - timedelta(days=1)).isoformat()},
            {"travellers": 0}, {"travellers": 9}, {"travellers": -1},
        ):
            with self.subTest(changes=changes):
                response = self.client.post(self.create_url, self.payload(**changes))
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors)
                self.assertEqual(BookingRequest.objects.count(), 0)

    def test_invalid_phone_or_submission_key_is_rejected(self):
        for changes in ({"phone": "not a number"}, {"request_key": "forged"}):
            response = self.client.post(self.create_url, self.payload(**changes))
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
            self.assertEqual(BookingRequest.objects.count(), 0)

    def test_submission_key_cannot_be_reused_by_another_user(self):
        data = self.payload()
        self.client.force_login(self.other)
        response = self.client.post(self.create_url, data)
        self.assertContains(response, "This form has expired or is invalid.")
        self.assertEqual(BookingRequest.objects.count(), 0)

    def test_inactive_adventure_cannot_be_requested(self):
        Adventure.objects.filter(pk=self.adventure.pk).update(is_active=False)
        self.assertEqual(self.client.get(self.create_url).status_code, 404)

    def test_user_cannot_see_or_cancel_another_users_request(self):
        booking = self.make_booking()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(booking.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.get(reverse("bookings:cancel", args=[booking.reference])).status_code, 404)
        self.assertEqual(self.client.post(reverse("bookings:cancel", args=[booking.reference])).status_code, 404)
        response = self.client.get(reverse("bookings:list"))
        self.assertNotContains(response, booking.reference_code)

    def test_pending_cancellation_requires_post(self):
        booking = self.make_booking()
        cancel_url = reverse("bookings:cancel", args=[booking.reference])
        self.assertEqual(self.client.get(cancel_url).status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingRequest.Status.PENDING)
        self.assertRedirects(self.client.post(cancel_url), booking.get_absolute_url())
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingRequest.Status.CANCELLED)

    def test_confirmed_cancellation_respects_fifteen_day_boundary(self):
        for days, allowed in ((15, True), (14, False)):
            booking = self.make_booking(status=BookingRequest.Status.CONFIRMED, travel_date=timezone.localdate() + timedelta(days=days))
            self.client.post(reverse("bookings:cancel", args=[booking.reference]))
            booking.refresh_from_db()
            self.assertEqual(booking.status, BookingRequest.Status.CANCELLED if allowed else BookingRequest.Status.CONFIRMED)

    def test_closed_requests_cannot_be_cancelled(self):
        for status in (BookingRequest.Status.CANCELLED, BookingRequest.Status.DECLINED):
            booking = self.make_booking(status=status)
            self.assertFalse(booking.can_cancel)
            self.client.post(reverse("bookings:cancel", args=[booking.reference]))
            booking.refresh_from_db()
            self.assertEqual(booking.status, status)

    def test_booking_post_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(self.create_url, self.payload())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(BookingRequest.objects.count(), 0)

    def test_admin_confirmation_only_updates_pending_future_requests(self):
        pending = self.make_booking()
        cancelled = self.make_booking(status=BookingRequest.Status.CANCELLED)
        past = self.make_booking(travel_date=timezone.localdate() - timedelta(days=1))
        self.client.force_login(self.staff)
        response = self.client.post(reverse("admin:bookings_bookingrequest_changelist"), {
            "action": "confirm_requests", "_selected_action": [pending.pk, cancelled.pk, past.pk],
        })
        self.assertEqual(response.status_code, 302)
        pending.refresh_from_db()
        cancelled.refresh_from_db()
        past.refresh_from_db()
        self.assertEqual(pending.status, BookingRequest.Status.CONFIRMED)
        self.assertEqual(cancelled.status, BookingRequest.Status.CANCELLED)
        self.assertEqual(past.status, BookingRequest.Status.PENDING)
