# Adventure Nepal

A server-rendered Nepal adventure planning application built with Django 6,
SQLite, Django templates, and vanilla CSS/JavaScript. Travelers can discover
adventures, browse destinations and travel stories, explore a photo gallery,
manage their accounts, and submit and track booking requests. Staff manage
content, inquiries, and booking status through Django admin.

## Local setup (PowerShell)

Requires Python **3.12 or newer**. There is no Node build step.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create a local `.env` using the names in `.env.example`. Generate a secret with:

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Put the generated value in `SECRET_KEY` in your private `.env`. Use a distinct
secret for production. Local commands explicitly default to development;
`DEBUG` in `.env` does not override that development module.

For a new database, apply migrations, then optionally seed the catalog:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_adventures
.\.venv\Scripts\python.exe manage.py seed_blog
.\.venv\Scripts\python.exe manage.py seed_gallery
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

All seed commands preserve existing records, including editorial edits and
archived adventures. They add missing seed records only. Back up an existing
database and media before deployment or operational changes. The active SQLite
database is `db.sqlite3` at the repository root; `config/db.sqlite3` is not used
by the settings. Do not delete either file based solely on its location.

## Architecture

| Location | Responsibility |
| --- | --- |
| `apps/core` | Home/support pages, contact messages, gallery, shared forms, POST throttling |
| `apps/adventures` | Regions, activities, catalog, dependent filtering, pricing display |
| `apps/destinations` | Region pages using the existing adventure models |
| `apps/blog` | Published/scheduled stories, categories, search |
| `apps/accounts` | Django authentication, registration, profiles, password recovery |
| `apps/bookings` | Ownership-scoped requests, price snapshots, status filtering, cancellation |
| `config/settings` | Shared, development, and production settings |
| `templates`, `static` | Shared design system and progressive UI behavior |

Booking requests are **not paid reservations**. Staff confirm arrangements
directly. Pending requests can be cancelled before departure; confirmed
requests require at least 15 days' notice for online cancellation. Pricing,
ownership, and status are set server-side. Signed submission keys prevent
duplicate booking creation, and price/title snapshots preserve request history.

## Verification

```powershell
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe -m pip check
```

Tests use a separate test database. Seed-image tests use temporary media storage.
They cover accounts and password recovery, publication rules, catalog boundaries
and facets, contact/gallery flows, booking integrity and ownership, cancellation,
status filtering, pagination, repeatable seeding, CSRF, and submission limits.

## Deployment

1. Set `DJANGO_SETTINGS_MODULE=config.settings.production`, a strong secret,
   `ALLOWED_HOSTS` containing your real hostnames (no scheme), and
   `CSRF_TRUSTED_ORIGINS` containing trusted HTTPS origins if needed.
2. Configure real SMTP delivery for password recovery. Console email is only
   useful locally. Store all credentials outside version control.
3. Configure HTTPS at your web server. WSGI/ASGI entry points default to production.
   Set `TRUST_PROXY_HTTPS=True` **only** when the proxy removes client-provided
   `X-Forwarded-Proto` and sets its own value. HTTPS redirects and secure cookies
   are enabled by default.
4. HSTS starts at one hour and does not cover subdomains or preload by default.
   Enable subdomain coverage only after every affected subdomain supports HTTPS.
   Preloading is a deliberate domain-wide operational decision, not enabled here.
5. Run migrations and `manage.py collectstatic --noinput`. Serve `staticfiles/`
   and uploaded media using the deployment web server/storage; Django only serves
   media in development. Keep uploaded media separate from executable application
   content, ideally on a dedicated media origin. Only staff upload images today.
6. Use a shared cache with atomic increment support for multiple application
   workers, or enforce equivalent rate limits at your trusted reverse proxy.
   `CACHE_BACKEND` and `CACHE_LOCATION` configure Django's cache. Redis/memcache
   backends need their corresponding client package installed by the deployment.
   The default local-memory cache has **per-process**, not deployment-wide limits.
7. Run the deployment check with production settings:

   ```powershell
   .\.venv\Scripts\python.exe manage.py check --deploy --settings=config.settings.production
   ```

POST throttling uses endpoint-specific fixed windows: login/admin login allow
10 attempts per 5 minutes; registration, password reset, and contact allow 5 per
10 minutes; booking submission allows 20 per 5 minutes. Limits apply to direct
client IPs, which are hashed before caching; forwarded IP headers are ignored.
Behind a proxy, set per-client limits at the edge to avoid sharing a proxy-IP
budget. `SUBMISSION_RATE_LIMITS` can be customized in settings. Blocked requests
return HTTP 429 with `Retry-After`. CSRF checks remain enabled and run first.

## Follow-up improvements

- Verify testimonial/marketing claims and replace editorial sample imagery with
  authorized brand assets. The current testimonial is static editorial content,
  not a database-backed review system.
- Plan explicit upload-size/image-dimension limits and responsive image derivatives.
- Resolve any existing duplicate emails before introducing database-enforced,
  case-insensitive uniqueness. Current form validation cannot prevent a concurrent
  race; an auth-model/schema change requires a separately reviewed migration plan.
- Add real availability, booking notifications, verified reviews, or calendar
  export when the operational requirements are clear.
- Evaluate PostgreSQL and shared caching when deployment concurrency warrants it.
- Lucide interface icons are served locally through `static/js/icons.js`, a
  licensed subset of Lucide 0.468.0. Add new icon definitions there when adding
  `data-lucide` names. Fonts and optional Font Awesome social-brand icons still
  use third-party CDNs.
