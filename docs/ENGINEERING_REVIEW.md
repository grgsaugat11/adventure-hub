# Engineering review and enhancement report

## Audit

The existing application is Django 6.0.7 with SQLite, six domain apps, Django
templates, vanilla JavaScript/CSS, and Django admin. Pillow supports uploaded
images and python-decouple loads environment configuration. REST Framework and
a PostgreSQL driver were installed locally but are not referenced by the active
application; they are not necessary to run it. The initial repository had no
dependency manifest or setup documentation.

Existing features include catalog search/facets/sorting/pagination, destination
pages, published and scheduled blog content, contact storage, a filtered gallery
with a native dialog viewer, registration/authentication/password recovery,
profiles, booking creation/tracking/cancellation, and content/booking admin.
There is no payment gateway or live inventory/availability service.

Strengths include domain separation, ORM queries, CSRF protection, authenticated
booking ownership checks, validated server-side booking fields, historical
pricing/title snapshots, signed idempotent booking submission, and existing
critical-workflow tests. All 65 baseline tests passed and recorded migrations
were already applied with no model/migration drift.

Problems identified included incomplete deployment configuration, destructive
catalog reseeding, overlapping price filters, inconsistent facet aggregation,
unstable sort ties, insufficient contrast, missing mobile drawer keyboard
behavior, misleading testimonial navigation, automatic carousel motion,
unbounded gallery/region listings, unnecessary page assets, and no submission
throttling. Static marketing claims and the testimonial are editorial content;
they are not verified customer reviews.

## Prioritized delivery

### Critical — configuration and data integrity

- Production defaults enforce HTTPS redirects, secure session/CSRF cookies,
  one-hour HSTS, and a strict-origin referrer policy.
- Hosts, trusted origins, proxy HTTPS trust, HSTS scope, and cache configuration
  are environment-driven. Forwarded HTTPS headers are trusted only when explicitly
  configured for a controlled proxy.
- WSGI/ASGI default to production; local management commands remain development.
- `STATIC_ROOT` is configured and generated assets are ignored by Git.
- Catalog reseeding adds missing entries and preserves edited names, prices,
  images, publication status, regions, and activity assignments.

### High — browsing accuracy, accessibility, and abuse resistance

- Price buckets are disjoint and agree across labels, filters, and SQL counts.
  Currency display preserves cents rather than rounding booking prices.
- Facets exclude their own selected criterion while retaining other criteria.
  Aggregation clears default model ordering to avoid split groups, and distinct
  counts prevent many-to-many overcounting. Empty activity options are excluded.
- Catalog sorting has a unique primary-key tie-breaker.
- The original green branding is refined for accessible contrast. Cards have
  consistent layout, subtle elevation, readable difficulty badges, and aligned
  actions. Compact navigation prevents intermediate-width collisions.
- Shared drawers isolate background content, manage keyboard focus, restore
  focus, expose expanded state, close on Escape/backdrop, and reset on breakpoint
  changes. CSS visibility transitions no longer delay initial focus.
- Global skip navigation, focus indicators, and reduced-motion styles apply
  throughout the app. FAQ details/summary elements work without JavaScript.
- Per-endpoint cached POST limits protect login/admin login, registration,
  password recovery, contact, and booking submission. Blocked requests receive a
  branded HTTP 429 page and a `Retry-After` header. CSRF remains ahead of throttling.
  Cache identifiers use hashed direct client IPs and do not trust forwarded IPs.

### Medium — useful workflow and performance improvements

- Booking status filters show counts scoped to the logged-in traveler, preserve
  filters across pagination, and provide appropriate filtered empty states.
- Gallery results paginate at 12; region adventures paginate at 9. Total counts
  remain accurate and category selections survive pagination.
- POST forms show a busy state and prevent repeated client submission while
  preserving Django validation and existing server-side booking idempotency.
- The carousel is manually controlled with accessible slide selection and inert
  inactive slides; controls disappear for a single slide.
- Inactive testimonial arrows were removed after confirming only one testimonial
  existed. Its unrelated anime portrait was replaced with an initials avatar;
  testimonial text and the original asset remain preserved.
- Inactive adventures no longer produce broken detail links from historical
  booking summaries. Adventure overview paragraph formatting remains HTML-escaped.
- Shared CSS loads via direct links without import chains. Route-specific styles
  and homepage scripts load where applicable; empty scripts are no longer fetched.
- Lucide is version-pinned, scripts are deferred, and icon initialization tolerates
  a missing CDN. Hero image priority and below-the-fold loading are appropriate.
- Branded 403/404/429/500 templates and setup/deployment documentation were added.

## Files affected

- Configuration: `config/settings/{base,development,production}.py`,
  `config/{wsgi,asgi}.py`, `.gitignore`, `.env.example`.
- Catalog: `apps/adventures/{models,filters,views,tests}.py`,
  `apps/adventures/management/commands/seed_adventures.py`.
- Other app behavior/tests: `apps/bookings/{views,tests}.py`,
  `apps/core/{views,middleware,tests}.py`,
  `apps/destinations/{views,tests}.py`, `apps/accounts/tests.py`.
- Shared templates: `templates/base.html`,
  `templates/includes/{navbar,page_styles,pagination}.html`,
  `templates/errors/base.html`, `templates/{403,404,429,500}.html`.
- Pages/components: booking create/detail/list, home, gallery, adventure
  list/detail, destination detail, adventure card, hero, FAQ, featured adventures,
  and testimonial templates.
- UI assets: shared CSS and responsive rules; adventure/booking page CSS;
  hero/featured/destination/testimonial/FAQ/footer/blog/CTA section CSS;
  `static/js/{main,navbar,adventures,home,faq}.js`.
- Handoff: `requirements.txt`, `README.md`, and this report.

No database schema changes or migrations are required. The application database,
uploaded media, private `.env`, and existing Word report were not edited.

## Verification performed

- Django suite: **82 tests passed**, including 17 added regressions for facet
  boundaries/aggregation, safe reseeding, throttling/CSRF, status-filter ownership,
  pagination, and error rendering.
- Migration dry-run: no model changes detected.
- Dependency check: no broken requirements.
- Static collection dry-run: 180 files resolved successfully.
- Chromium browser checks: **84 page/viewport combinations** at 320, 390, 768,
  and 1440 pixels (56 public and 28 authenticated), with no horizontal overflow
  or uncaught JavaScript errors in the checked pages.
- Public checks covered home, catalog, destinations, blog, about, contact,
  gallery, privacy, login/signup/reset, and adventure/region/story detail pages.
- Authenticated checks used a separate temporary database and covered profile,
  booking lists/status pagination, booking creation/detail/cancellation, and
  password-change page rendering. Login, profile editing, live group totals,
  submission, cancellation, filtered pagination, and logout passed in Chromium.
- Navigation/filter focus behavior, search, sorting, FAQ, carousel selection,
  gallery dialog, and JavaScript-disabled FAQ/search were exercised.
- Axe-core WCAG 2 A/AA and WCAG 2.1 AA scans reported **zero automated violations**
  on the checked public and authenticated pages at mobile/desktop sizes. This is
  automated evidence, not a claim of full accessibility certification.
- Production smoke confirmed HTTP redirects, HTTPS template rendering, HSTS,
  and secure-cookie configuration. With ephemeral strong-secret/host overrides,
  deployment checks retained only intentional HSTS subdomain/preload advisories.
- Browser tooling and isolated fixtures were installed/created in the approved
  temporary directory, not as application dependencies.

## Remaining work and deployment requirements

1. The existing local secret is still flagged by Django's deployment check.
   Generate a distinct strong production secret and set actual allowed hosts;
   private environment values were deliberately not replaced.
2. Configure SMTP, TLS termination, static/media serving, monitoring, backups,
   and shared-cache or edge-level throttling for the actual deployment.
   Local-memory rate budgets are process-local. Behind a proxy, edge limits
   should distinguish client IPs rather than sharing the proxy address budget.
3. HSTS subdomain coverage/preloading remain intentional domain-wide decisions.
   Their Django advisories are not silenced.
4. Add explicit image upload-size/dimension controls and responsive derivatives.
   Current uploads are staff-only and use Django ImageFields; live storage and
   malicious-upload scenarios were not penetration-tested.
5. Plan database-enforced email uniqueness after reviewing existing duplicates
   and the auth-model migration strategy. Form validation alone has a race.
6. Verify testimonial/marketing claims and replace sample editorial content with
   authorized real content. No reviews, payments, or availability were fabricated.
7. Real SMTP delivery, distributed-cache concurrency, deployed proxy/CDN behavior,
   Safari/Firefox, and manual screen-reader testing remain unverified.

See `README.md` for setup, operational commands, configuration, and next steps.
