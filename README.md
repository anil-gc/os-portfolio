# Portfolio OS

A React portfolio with a desktop-inspired workspace and a Django REST Framework
content backend. All personal details, projects, skills, work experience,
education, certificates, and resume records are editable in Django admin.
Contact submissions are stored in a private admin inbox.

The local profile and hosted preview now contain Anil GC's conversation-backed
project information. Unverified contact details, location, credentials, and
proficiency claims are omitted. Original sample records remain unpublished in
admin; `frontend/data/demo.json` is only the optional seed fixture. The saved
preview snapshot is `frontend/data/portfolio.json`.

## Run Locally

The current workspace has dependencies, migrations, sample content, and a local
admin account already prepared. Local URLs:

- React: http://127.0.0.1:5173/
- Django admin: http://127.0.0.1:8000/admin/
- Custom dashboard: http://127.0.0.1:8000/dashboard/
- Public portfolio: http://127.0.0.1:8000/api/v1/portfolio/site/
- Health: http://127.0.0.1:8000/api/v1/core/health/

The generated local admin credentials are in `.venv/portfolio-admin.txt`, which
is ignored by source control and excluded from container images. Use them only
locally. Create a separate production administrator with `createsuperuser`.

For a fresh checkout, use Python 3.13 or 3.14 and Node.js 22.13+ (Node 24 recommended):

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py seed_portfolio frontend/data/demo.json
.venv\Scripts\python.exe manage.py createsuperuser
.venv\Scripts\python.exe manage.py runserver
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Copy environment examples only when the destination does not already exist.
Seeding is transactional and refuses to overwrite an existing profile. It is
optional: you can enter all your content directly in admin instead.

## Edit the Portfolio

### Custom Dashboard (Tasks 1, 2 and 3)

Open `/dashboard/` on the Django server and sign in with your existing active
staff account. The custom sign-in page, responsive workspace shell, accessible
mobile navigation, and POST-only logout are implemented. The overview shows live
project, skill, certificate, experience, and contact-message totals, including
published/draft counts and unread messages. Recent lists show up to four projects
by modification date and four messages by submission date. Message email addresses
and bodies are not fetched or shown on the overview.

Summaries and recent content require the corresponding view or change permission.
Projects are managed directly in the custom dashboard; other quick actions open
existing Django admin forms with the relevant permissions. The profile action
offers setup if no profile exists. Counts use one aggregate query per model; recent lists are
limited queries with only the displayed fields. No dashboard caching is added.

Every dashboard content view uses `DashboardAccessMixin` to enforce active staff
access on the server. Future views can declare `permission_required` using existing
Django model permissions. Anonymous users go to login; unauthorized users get 403.
Login and logout use Django sessions and CSRF protection. Private responses are
not cached. Failed sign-ins are limited to 10 per client IP per five-minute cache
window; this is best-effort abuse control, shared across workers when Redis is used.

`DASHBOARD_PUBLIC_SITE_URL` controls the "View portfolio" links: local settings
default to `http://127.0.0.1:5173/`, and production defaults to `/`. Start the React
development server separately to use those links locally. The dashboard itself
needs only Django and its app-local static assets; no frontend build is required.

The first dashboard task adds no models, migrations, or dependencies. It does not
change existing portfolio records or the public API. Dashboard tests run with:

```powershell
.venv\Scripts\python.exe manage.py test apps.dashboard
```

### Manage Content in Django Admin

Projects can now be managed without Django admin:

- `/dashboard/projects/`: all projects, search by title/category, publication
  filters, and pagination (10 per page), ordered by display order then ID.
- `/dashboard/projects/new/`: create a project.
- `/dashboard/projects/<id>/edit/`: edit all existing model fields.
- `/dashboard/projects/<id>/delete/`: review confirmation, then delete with POST.

Listing requires `view_project` or `change_project`; create, edit, and delete
require `add_project`, `change_project`, and `delete_project` respectively, in
addition to active staff access. Mutations require CSRF-protected POSTs. The shared
ModelForm validates fields on the server. Technologies use one entry per line;
an empty slug is generated from the title and duplicate slugs show a field error.

The existing model stores `image_url`, not an uploaded file. The dashboard supports
HTTP/HTTPS image URLs, previews, replacement, and clearing; it does not upload or
delete files. Keep the current URL unchanged to retain an image.

Publishing writes to the same Project records used by both public APIs. Drafts
stay private. The public frontend loads current data on page load, manual refresh,
and when returning to a visible/focused tab. No rebuild is required for content
changes. A disconnected static preview still cannot synchronize with the database.

The existing Django admin remains available for all content:

1. Open Django admin and update the single profile, including name, headline,
   location, intro, bio, about text, email, social links, avatar URL, and availability.
2. Edit or delete the sample domain records. Publish records to make them public;
   drafts are excluded from every public API. Sort order controls display order.
3. Mark projects as featured to include them on the overview. Add image URLs,
   live URLs, and source URLs when available. Blank links are omitted in React.
4. Upload a PDF to a published resume record, or use the frontend's printable
   resume generated from your published content. Resume uploads are limited to 5 MB.
5. Turn off the profile's demo flag only after replacing all sample credentials
   and content. Refresh the frontend or use Preferences > Refresh content.
6. Read contact submissions under Contact > Messages. Messages are never publicly
   listed. The form saves to the inbox; it does not send email or subscribe anyone.

The sample projects, employers, education, and certificates are fictional.
The UI labels sample content, and search indexing is disabled until launch.

## Architecture

`config/` owns settings, entry points, URL composition, and deployment concerns.
`apps/` contains first-party domains. Each domain owns its models, admin, serializers,
and public URL module. `core` owns abstract timestamps, publication infrastructure,
shared validation, and process liveness. The `portfolio` app composes the public
site snapshot through each domain's serializer. No generic catch-all content table
or JSON blob replaces the domain model.

The frontend lives in `frontend/`, separately from Python configuration. It uses
React, TypeScript, the generated Vinext/Vite build, and existing Base UI/Shadcn
primitives for dialogs, search, sidebar, tabs, switches, and checkboxes. The final
output is static HTML/CSS/JavaScript in `frontend/dist/client`; Node is only needed
to develop and build it. Domain data is loaded at runtime from Django, so publishing
content does not require rebuilding the frontend.

The desktop shell owns navigation, theme, window state, and search. Presentation
panels stay in `components/portfolio-panels.tsx`; API and URL handling stay in
`lib/portfolio.ts`. Hash URLs support direct links, project details, and browser
history without requiring extra backend page routes. Native scrolling and a compact
navigation rail keep the same content available on mobile. Theme preferences use
device-local storage; portfolio data and contact messages stay in Django.

### APIs and Permissions

All API routes live under `/api/v1/`. Existing nested app namespaces and DRF
`NamespaceVersioning` are preserved. For example, Django reverses
`v1:portfolio:site`, while DRF reverses `portfolio:site` with a request.

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/v1/core/health/` | GET | Database-independent process liveness |
| `/api/v1/portfolio/site/` | GET | Public portfolio snapshot |
| `/api/v1/projects/` | GET | Published projects |
| `/api/v1/skills/` | GET | Published skills |
| `/api/v1/experience/` | GET | Published experience |
| `/api/v1/education/` | GET | Published education |
| `/api/v1/certificates/` | GET | Published certificates |
| `/api/v1/resume/` | GET | Published resume records |
| `/api/v1/contact/` | POST | Store a validated contact message |

Content management uses Django admin's session authentication and CSRF protection.
New DRF views remain staff-only by default. Public read views and the contact
create view explicitly override that default. There is no public content-writing
or message-listing API. Public views skip session authentication to avoid coupling
anonymous reads to admin cookies.

The contact API validates lengths and email format, rejects a honeypot, and limits
submissions to five per IP per hour. Production Compose uses a shared Redis cache
so workers share throttle state. DRF throttling is best-effort rather than a strict
security boundary; add edge abuse controls or CAPTCHA if actual traffic requires it.
See [DRF throttling](https://www.django-rest-framework.org/api-guide/throttling/).

### Data and Deployment Settings

Every domain model inherits timestamp fields directly or through the abstract
publication base. `QuerySet.update()` and `bulk_update()` bypass `auto_now`, so
future bulk changes must set modification timestamps explicitly. Date constraints
are enforced both in admin validation and in the database. Profile cardinality is
enforced with a single allowed primary key, and draft content defaults to private.

Local settings use SQLite and allow loopback hosts. Production requires a strong
secret, explicit hosts, and a database URL; debug cannot be enabled there. ASGI/WSGI
default to production, while management commands default to local. Set
`DJANGO_SETTINGS_MODULE` in the process environment before Django starts.

Static assets are collected separately from uploaded media. Caddy serves both in
production; uploaded resumes are delivered as attachments with `nosniff`. The API
server is not exposed directly. Only the trusted proxy can set the HTTPS forwarding
header. HSTS subdomains and preload remain opt-in, which intentionally leaves
`security.W005` and `security.W021` warnings until the domain policy is verified.

### Standalone Preview Versus Live Site

`VITE_API_BASE_URL` defaults to `/api/v1`. The local development server proxies API
and media requests to Django at port 8000. Production Caddy serves React and Django
under one HTTPS origin, avoiding broad CORS configuration and cross-origin admin
cookies.

A standalone hosted React preview can show `data/portfolio.json` when no Django API
is attached and `VITE_ALLOW_DEMO_FALLBACK=true`. This offline mode is visibly marked and
disables message submission. It does not synchronize with your local admin.
The production container sets fallback to false and shows an honest unavailable
state if Django cannot be reached. A Sites static deployment hosts the frontend
only; full Django hosting requires the deployment setup below.

## Full Production Deployment

See [deploy/README.md](deploy/README.md) for domain setup, HTTPS, PostgreSQL,
Redis, content seeding, administrator creation, and backups. Compose keeps data,
media, collected static files, and TLS certificates in persistent volumes.
No server credentials or domain have been assumed or published.

## Verification

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py test
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
cd frontend
npm run typecheck
npm run lint
npm run build
npm audit
```

The linter checks authored code; unmodified generated UI primitives and the
generated mobile hook are excluded. Backend tests cover publication boundaries,
read-only APIs, admin-to-API changes, contact creation/validation/throttling,
namespace versioning, and production settings. Browser interaction testing and
the complete Docker runtime remain separate deployment validation steps.

The frontend dependency lockfile is committed with the site. Python requirement
ranges allow maintained updates; resolve and lock Python packages for your release
platform before production rollout. The wallpaper is an original generated asset,
optimized to WebP. Social-preview imagery has not been added.
