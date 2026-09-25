# Task 7 — Contact Messages Management

Completed September 25, 2026. No subsequent task has started. All existing
uncommitted Tasks 4–6 work was preserved. No commit, push, or deployment was made.

## Architecture inspected before changes

The public React Contact panel submits JSON to `POST /api/v1/contact/`. Django
REST Framework's MessageCreateView validates it through MessageSerializer and
saves the existing `apps.contact.models.Message` model. Messages were already
stored in the database, with name, email, subject, message, timestamps, and an
`is_read` flag defaulting to false. Local storage is SQLite; production supports
the configured PostgreSQL database. There is no email sending, third-party form
service, mailing-list subscription, or browser-side message storage.

The form already had required fields, email/length checks, consent UI, and a
honeypot. The API already enforced model field validation, honeypot rejection,
and ScopedRateThrottle at five attempts per hour. Production configuration uses
the existing shared Redis cache. No new anti-spam service was needed.

The dashboard overview already queried real totals, unread counts, and the four
most recent messages, without selecting email addresses or bodies. Its links
opened Django Admin. The existing dashboard uses templates, sessions,
DashboardAccessMixin, model permissions, CSRF, private response headers, reusable
form/card/empty-state styles, and a responsive sidebar. Before changes, all 201
existing backend tests passed.

## Implemented workflow

Public React form → existing DRF validation/throttle → existing Message table →
authenticated dashboard list → detail → explicit status change or confirmed delete.

The list shows newest messages first, with a primary-key tie breaker, 10 entries
per page, sender name/email, subject, a preview of at most 180 characters,
submission date/time with timezone, and read/unread status. The database selects
only the preview substring for list pages instead of full message bodies.

Search matches sender, email, or subject. All/Unread/Read filters combine with
search, and pagination preserves those filters. Clear empty and no-match states
use the existing dashboard component. No fake messages or analytics are added.

Details show the full plain-text message with preserved line breaks and wrapping
for long unbroken text. Opening a message does not mark it read. Mark as Read
and Mark as Unread are explicit, repeatable POST actions. They update only status
and modification time; sender text and original received time are preserved.

Delete opens a confirmation page. Cancel returns to the intact detail page.
Only a CSRF-protected POST removes the message, then redirects to the list with
success feedback. No automatic reply, mailto link, email client, or notification
system was added.

## Routes

| Route | Methods | Purpose |
| --- | --- | --- |
| `/api/v1/contact/` | POST, OPTIONS | Existing public submission endpoint |
| `/dashboard/messages/` | GET, HEAD | Private list, search, filters, pagination |
| `/dashboard/messages/<id>/` | GET, HEAD | Private message detail |
| `/dashboard/messages/<id>/status/` | POST | Explicit read/unread update |
| `/dashboard/messages/<id>/delete/` | GET, HEAD, POST | Confirmation on GET; deletion on POST |
| `/dashboard/` | GET | Existing real counts and recent entries with custom inbox links |

Authenticated OPTIONS handling is also available through Django's class-based
views. Public contact GET returns 405; no public contact-detail route exists.

## Model and migration changes

None. The existing Message model, table, timestamps, and read flag are reused.
No new fields, dependencies, storage mechanism, or service were introduced.
Django Admin remains available as an internal fallback.

Two small public-flow improvements accompany the inbox:

- Server validation enforces the existing frontend's message minimum of 10
  characters, alongside the existing 5,000 maximum. Name is required (100 max),
  email must be valid (254 max), and subject is required (160 max).
- HTTP 201 returns only `{"detail": "Message received."}`, with no message
  content or internal ID. The frontend already relies on status for success.
  Non-validation server failures display a generic error; 400 field errors and
  the existing 429 feedback remain useful. Public form design is unchanged.

## Security and privacy

- Every management route requires an authenticated, active staff account.
- Lists/details require `contact.view_message` or `contact.change_message`.
- Status changes require `contact.change_message`.
- Deletion requires `contact.delete_message` plus view/change permission.
  Delete-only permission cannot disclose contact data through confirmation pages.
- Unauthorized access is rejected before looking up the requested ID. Anonymous
  visitors go to login; unauthorized staff receive 403.
- Private responses use `never_cache`, and templates retain noindex/nofollow.
- Mutations require POST and CSRF. GET/HEAD never mark read or delete. Status
  accepts only `read` or `unread`; arbitrary posted content cannot edit messages.
- Django escapes visitor text; no `safe`, raw HTML rendering, or automatic link
  conversion is used. Detail content wraps and preserves plain-text line breaks.
- The public submission endpoint has no authenticated-session authority and no
  read/update/delete API. Submissions cannot set IDs or read status. Honeypot,
  input limits, and existing throttling are retained.
- No new personal fields or custom sender/body logging were added. Overview
  queries still select only name, subject, received time, and read status.
- Public portfolio serializers never include messages. The only public success
  response is the receipt acknowledgement for the visitor's submission.

The existing throttle remains best-effort abuse protection, not a strict global
quota under concurrent requests. Production requires its already configured
shared cache for consistent worker behavior.

## Files changed

New:

- `apps/dashboard/message_views.py` — list/detail/status/delete views.
- `apps/dashboard/templates/dashboard/messages/base.html`.
- `apps/dashboard/templates/dashboard/messages/list.html`.
- `apps/dashboard/templates/dashboard/messages/detail.html`.
- `apps/dashboard/templates/dashboard/messages/status.html`.
- `apps/dashboard/templates/dashboard/messages/confirm_delete.html`.
- `apps/dashboard/static/dashboard/messages.css` — responsive inbox styles.
- `apps/dashboard/tests/test_messages.py` — 27 management/integration tests.
- `docs/TASK7_MESSAGES_HANDOFF.md`.

Updated:

- `apps/dashboard/urls.py` — four message routes.
- `apps/dashboard/overview.py` — count-card link to the inbox.
- `apps/dashboard/templates/dashboard/home.html` — recent/detail links.
- `apps/dashboard/templates/dashboard/shell.html` — permission-aware Messages nav.
- `apps/contact/serializers.py` — existing 10-character UI minimum enforced server-side.
- `apps/contact/views.py` — receipt-only success response.
- `apps/contact/tests.py` — five additional validation/privacy tests.
- `frontend/components/portfolio-panels.tsx` — generic feedback for non-400/429 errors.
- `README.md`, `deploy/README.md`, `docs/DASHBOARD_HANDOFF.md` — current usage/handoff.

## Automated checks

| Command | Actual result |
| --- | --- |
| `.venv\Scripts\python.exe manage.py test` before changes | 201 tests passed in 20.280s |
| `.venv\Scripts\python.exe manage.py test apps.contact apps.dashboard.tests.test_messages apps.dashboard.tests.test_overview` | 47 tests passed in 1.407s |
| `.venv\Scripts\python.exe manage.py test` after changes | 233 tests passed in 18.891s |
| `.venv\Scripts\python.exe manage.py check` | No issues |
| `.venv\Scripts\python.exe manage.py makemigrations --check --dry-run` | No changes detected |
| Frontend `npm run typecheck` | Passed |
| Frontend `npm run lint` | Passed |
| Frontend `npm run build` | Passed; static export completed |
| `git diff --check` | Passed |

No backend lint configuration is present. The build produced non-failing Node
glob experimental/plugin timing notices. Docker/production runtime was not tested.

Tests cover the complete public submission→database→private dashboard path;
required fields, whitespace, lengths, email, honeypot, throttling; anonymous,
nonstaff, inactive, view-only, change-only, and delete-only permissions; CSRF;
safe/idempotent state updates; confirmation/deletion; missing IDs; escaped scripts;
bounded previews and query count; ordering/pagination/filter preservation; empty
states; navigation; live overview counts and privacy; and public API isolation.

## Browser verification

Used the production frontend build at port 5177 and isolated Django/database at
8007. Public and dashboard browsers had separate sessions. The public session had
no admin session cookie; the dashboard used an authenticated owner session.

1. Entered an invalid email in the real public form. Confirmed native email
   invalidity, then deliberately bypassed native validation to exercise the
   backend. The real POST returned 400 and the form showed a clear email error.
   The dashboard still showed zero messages.
2. Corrected the email and submitted the same form. The actual POST returned 201,
   only the receipt acknowledgement, and the public UI showed Message received.
3. Reloaded the dashboard: one new message, marked Unread. Opened it and verified
   every submitted value, line breaks, full body, and escaped script-like text.
4. Marked it Read and refreshed; status persisted. Overview showed zero unread
   while retaining the message, without displaying email or full message text.
5. Marked it Unread and refreshed; status persisted. Email search plus Read/Unread
   filters returned the expected empty/matching states.
6. Opened Delete confirmation, cancelled, and verified the message still existed.
   Reopened confirmation and deleted it by POST. The list showed success plus
   the empty state; overview total/unread counts both returned to zero.
7. Anonymous HTTP checks returned login redirects for list/detail, 405 for public
   contact GET, and 404 for a guessed public contact-detail URL. No private
   content appeared in those responses or in the public portfolio API.
8. List and detail checked at 1440, 1024, 768, 390, and 320px: no horizontal
   document overflow, including a 240-character unbroken string. Mobile delete
   confirmation and empty state also fit. Inspected desktop/mobile screenshots.
   Mobile navigation opens, Escape closes it, and focus returns to its trigger.

The original SQLite database's SHA-256 remained unchanged after browser QA. The
test message was deleted from the isolated copy. Normal port 8000 loaded the new
Messages route and redirects anonymous visitors to login. No original contact
record was added, edited, or deleted.

Artifacts are in ignored `output/playwright/task7-*`; authentication state and
database copies must not be published. Browser coverage is Chromium, not a
physical-device/cross-browser certification. The pre-existing `/favicon.ico` 404
and deliberate invalid-submission 400 appeared in the public console; no stored
script executed.

## Smallest next improvement — not started

A read-only media inventory of the existing profile-photo and resume uploads:
show filename, size, and whether each file is currently referenced. Reuse existing
storage, with no bulk deletion or new upload platform in that first step.
General Settings, advanced analytics, email inbox integration, and notifications
remain outside this task.
