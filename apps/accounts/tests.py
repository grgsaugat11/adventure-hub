import re
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()
PASSWORD = "Forest-River-Blue!2026"


@override_settings(SUBMISSION_RATE_LIMITS={})
class AccountTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("traveller", "traveller@example.com", PASSWORD)
        cls.other = User.objects.create_user("other", "other@example.com", PASSWORD)

    def signup_data(self, **changes):
        return {"username": "newtraveller", "email": "New@example.com", "first_name": "New",
                "last_name": "Traveller", "password1": PASSWORD, "password2": PASSWORD, **changes}

    def test_signup_logs_in_and_preserves_local_next(self):
        response = self.client.post(reverse("accounts:signup"), self.signup_data(next=reverse("core:contact")))
        self.assertRedirects(response, reverse("core:contact"))
        user = User.objects.get(username="newtraveller")
        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_signup_rejects_external_redirect(self):
        response = self.client.post(reverse("accounts:signup"), self.signup_data(next="https://outside.example/"))
        self.assertRedirects(response, reverse("accounts:profile"))

    def test_signup_rejects_duplicate_email_case_insensitively(self):
        response = self.client.post(reverse("accounts:signup"), self.signup_data(email="TRAVELLER@example.com"))
        self.assertContains(response, "An account already uses this email address.")
        self.assertFalse(User.objects.filter(username="newtraveller").exists())

    def test_signup_rejects_weak_or_mismatched_passwords(self):
        for password1, password2 in (("123", "123"), (PASSWORD, "Different!Password2026")):
            response = self.client.post(reverse("accounts:signup"), self.signup_data(password1=password1, password2=password2))
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
            self.assertFalse(User.objects.filter(username="newtraveller").exists())

    def test_login_and_external_next_protection(self):
        response = self.client.post(reverse("accounts:login"), {
            "username": "traveller", "password": PASSWORD, "next": "//outside.example/",
        })
        self.assertRedirects(response, reverse("accounts:profile"))

    def test_invalid_login_does_not_start_session(self):
        response = self.client.post(reverse("accounts:login"), {"username": "traveller", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertTrue(response.context["form"].non_field_errors())

    def test_profile_requires_login_and_only_edits_current_user(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:profile"), {
            "first_name": "Updated", "last_name": "Name", "email": "UPDATED@example.com", "is_staff": "true",
        })
        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.other.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.email, "updated@example.com")
        self.assertFalse(self.user.is_staff)
        self.assertEqual(self.other.email, "other@example.com")

    def test_profile_rejects_email_used_by_another_account(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:profile"), {"email": "OTHER@example.com"})
        self.assertContains(response, "An account already uses this email address.")
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "traveller@example.com")

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertRedirects(self.client.post(reverse("accounts:logout")), reverse("core:home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_password_change_preserves_session(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:password_change"), {
            "old_password": PASSWORD, "new_password1": "New-Woodland!Trail2026", "new_password2": "New-Woodland!Trail2026",
        })
        self.assertRedirects(response, reverse("accounts:password_change_done"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("New-Woodland!Trail2026"))
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 200)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_email_and_token_work_end_to_end(self):
        response = self.client.post(reverse("accounts:password_reset"), {"email": self.user.email})
        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        reset_url = re.search(r"https?://\S+", mail.outbox[0].body).group(0)
        response = self.client.get(urlparse(reset_url).path)
        self.assertEqual(response.status_code, 302)
        confirm_url = response.url
        response = self.client.post(confirm_url, {"new_password1": "Recovered-Woodland!2026", "new_password2": "Recovered-Woodland!2026"})
        self.assertRedirects(response, reverse("accounts:password_reset_complete"))
        self.assertTrue(self.client.login(username=self.user.username, password="Recovered-Woodland!2026"))
        self.client.logout()
        response = self.client.get(urlparse(reset_url).path)
        self.assertFalse(response.context["validlink"])

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_unknown_reset_email_does_not_reveal_account_existence(self):
        response = self.client.post(reverse("accounts:password_reset"), {"email": "missing@example.com"})
        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)
