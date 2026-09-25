# Deploy the Complete Portfolio

The React preview and the complete Django application have different hosting needs.
This setup runs both under one domain with Caddy HTTPS, Gunicorn, PostgreSQL, and
Redis. It requires a Linux host with Docker Compose and a public domain whose DNS
points to that host. Ports 80 and 443 must be reachable for certificate issuance.

## Prepare the Environment

Copy `deploy/.env.example` to `deploy/.env`, then supply your hostname and random
secrets. Generate two different URL-safe secrets with:

```sh
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Use a hostname such as `portfolio.yourdomain.com`, without a scheme, port, or path.
The database password is embedded in a connection URL, so use URL-safe characters.
Never commit the populated environment file. `.dockerignore` excludes it.

## Build and Initialize

Run from the repository root:

```sh
docker compose --env-file deploy/.env build
docker compose --env-file deploy/.env up -d database cache
docker compose --env-file deploy/.env run --rm backend python manage.py migrate
docker compose --env-file deploy/.env run --rm backend python manage.py collectstatic --noinput
docker compose --env-file deploy/.env run --rm backend python manage.py createsuperuser
docker compose --env-file deploy/.env run --rm backend python manage.py check --deploy
```

Optionally seed sample content on a new, empty installation:

```sh
docker compose --env-file deploy/.env run --rm backend python manage.py seed_portfolio demo.json
```

The seed never overwrites an existing profile. For a real launch, replace sample
content in admin or create your real profile directly, then disable the demo flag.
Start the site:

```sh
docker compose --env-file deploy/.env up -d
```

Open `https://YOUR_DOMAIN/admin/`, enter content, publish records, and verify the
public pages. Contact submissions appear in the admin inbox; no external mail
provider is required. Resume PDF files persist in the media volume. Backend, cache,
and database ports are internal to the Docker network.

The custom dashboard is available at `https://YOUR_DOMAIN/dashboard/`, using the
same active staff accounts. It includes sign-in/out, the responsive overview, and
custom project, skills, experience, education, certificates, and Profile/About
management. `/dashboard/profile/` includes photo and current resume uploads.
`/dashboard/messages/` provides the private contact inbox, explicit read/unread
actions, and confirmed deletion. It reuses the public contact API's Message table;
Task 7 adds no migration, service, or email delivery. Existing staff need contact
view/change permission, with separate change/delete permissions for mutations.
Install updated backend requirements, run migrations, and collect static files.
The optional profile image uses the existing media volume; PDFs retain the
attachment response policy. Public content now requires Django, with no bundled
personal-data fallback. Django Admin remains available for all existing models.
Rebuild the backend image and run `collectstatic` when updating dashboard templates
or assets. Rebuild the web image to pick up the `/dashboard` Caddy route.

Caddy overwrites `X-Real-IP` with the connecting client's address. Compose enables
`DASHBOARD_TRUST_PROXY_IP` so login throttling uses that trusted address. Keep this
setting false if Django is directly reachable, and do not trust client-supplied
headers. Adding another proxy/CDN requires reviewing the trusted client-IP setup.
The existing Redis cache shares sign-in failure counters between workers. Dashboard
public-site links default to `/` in production; override `DASHBOARD_PUBLIC_SITE_URL`
only if the public frontend lives at another URL.

## Before Announcing the Site

- Replace all dummy content, links, and the example email. Confirm projects and
  qualifications are accurate, published, and correctly ordered.
- Customize the title and description in `frontend/app/layout.tsx`. Set its robots
  metadata to allow indexing only after replacing the sample content, then rebuild
  the web image. Current metadata intentionally disables indexing.
- Verify login, an admin content edit, a contact submission, resume download,
  project links, mobile layout, keyboard navigation, and the public health URL.
- Review HSTS coverage. The two default subdomain/preload warnings are intentional;
  enable them only when all affected hosts support HTTPS.
- Set up encrypted database/media backups and check restoration. Monitor service
  restarts, request errors, disk usage, and the private contact inbox.
- Resolve Python requirements into a release lock and pin container image digests
  as part of your release process. The supplied image tags receive updates.

## Updates and Backups

Back up PostgreSQL before migrations. For example, from a POSIX shell:

```sh
docker compose --env-file deploy/.env exec -T database pg_dump -U portfolio portfolio > portfolio.sql
```

Also back up the media volume and keep deployment secrets in a separate secret
store. Rebuild images, run migrations and `collectstatic` once, then restart
services. Never use `docker compose down -v` unless you intend to delete all
database, media, and certificate volumes.

## Validation Status

Compose configuration is validated. The local Docker engine was not running when
this setup was prepared, so container builds, TLS issuance, and the full production
runtime have not been exercised. Local Django APIs, seeded data, the frontend build,
and automated backend checks are verified separately. No public Django deployment
has been provisioned by this repository alone.
