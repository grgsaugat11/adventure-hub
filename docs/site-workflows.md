# Accounts, bookings and support

## Local setup

Use the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_blog
.\.venv\Scripts\python.exe manage.py seed_gallery
.\.venv\Scripts\python.exe manage.py runserver
```

The seed commands preserve existing articles and gallery edits.

## Accounts

- `/accounts/signup/`: create an account and sign in.
- `/accounts/login/`: sign in; a booking destination is preserved through login/signup.
- `/accounts/`: edit your name/email, change your password, or sign out.
- `/accounts/password/reset/`: recover access by email.
- Logout accepts POST requests only.

Password recovery uses Django's expiring, single-use reset tokens. Local email is printed in the terminal. For real delivery, set these values in the environment or `.env`:

```text
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your-mail-server
EMAIL_PORT=587
EMAIL_HOST_USER=your-mail-user
EMAIL_HOST_PASSWORD=your-mail-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=your-sender-address
```

## Booking requests

Travellers choose an active adventure, sign in, select a future preferred date and group size, and submit contact details. The page estimates the total, but the server determines the stored price. Trip title, duration, unit price and currency are saved with the request so catalogue edits do not change an existing estimate.

- `/bookings/`: the signed-in traveller's requests.
- `/bookings/new/<adventure-slug>/`: submit a request.
- `/bookings/<reference>/`: status, contact details and estimated cost.
- `/bookings/<reference>/cancel/`: cancellation confirmation.

Requests start **Under Review**. This does not reserve inventory or collect payment. The team checks availability and arranges payment directly. Duplicate submissions of one form create one request.

In `/admin/`, open **Booking requests** to review requests and internal notes. Confirm or decline pending requests individually or with the list actions. Cancelled requests and past dates are excluded from the bulk confirmation action.

Travellers can cancel pending requests before the preferred date. Confirmed requests can be cancelled online at least 15 days before departure; closer changes go through Contact. Booking pages are restricted to their owner.

## Contact and gallery

- `/contact/`: messages are stored under **Contact messages** in the admin. The team replies using the submitted email and can mark messages In Progress or Closed.
- `/gallery/`: filter photos by category, open the viewer and navigate with buttons or arrow keys. Escape closes it. The admin supports uploaded photos, captions, ordering and active/inactive visibility.
- `/privacy/`: describes the information handled by these features.

Optional contact/social configuration:

```text
SITE_CONTACT_EMAIL=your-contact-address
SITE_CONTACT_PHONE=your-real-phone-number
INSTAGRAM_URL=https://www.instagram.com/your-profile/
FACEBOOK_URL=https://www.facebook.com/your-page/
YOUTUBE_URL=https://www.youtube.com/@your-channel
```

Phone and social links appear when configured. No fabricated phone number or social profile is linked.
