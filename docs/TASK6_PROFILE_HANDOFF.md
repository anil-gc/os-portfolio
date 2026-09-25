# Task 6 — Profile / About Management

Completed September 25, 2026. Task 7 has not started. Existing uncommitted Tasks
4–5 files were preserved. No commit, push, or production deployment was performed.

## Inspection and previous sources

Before implementation, the full existing suite passed: 172 tests. The dashboard
already used Django templates, session authentication, DashboardAccessMixin,
model permissions, CSRF, private no-cache responses, and shared form components.
Django Admin remains the fallback.

| Content | Previous source | Current source / public use |
| --- | --- | --- |
| Name | Singleton Profile plus bundled owner snapshot and hardcoded metadata | Profile.name; identity, page title, sidebar, About, resume |
| Professional headline | Profile.headline plus bundled snapshot | Same field; sidebar, About, resume |
| Hero heading | Profile.intro plus snapshot | Same field; Overview main heading |
| Short introduction | Profile.bio plus snapshot | Same field; Overview and client description metadata |
| Full About | Profile.about plus snapshot | Same field; About paragraphs |
| Location / public email | Profile fields plus snapshot | Same fields; existing conditional displays |
| GitHub / LinkedIn | Profile URL fields plus snapshot | Same fields; Contact links, hidden when empty |
| Availability / sample labels | Profile.available / is_demo plus snapshot | Same fields; existing status and labels |
| Profile image | Profile.avatar_url; initials when blank | New optional Profile.avatar upload takes priority over existing URL |
| Resume | Existing Resume model, FileField, serializer, published selection | Same record, edited in Profile page; existing Open PDF action |
| CTA labels / decorative copy | Fixed React interface text | Preserved as interface copy; no new CTA fields |
| Hero image | No separate owner hero-image field in the design | No extra field introduced |
| Owner snapshot | frontend/data/portfolio.json used during loading/offline | Removed; loading/unavailable state uses no personal fallback |
| Example seed | frontend/data/demo.json | Still an optional explicit seed and type-only import; never runtime content |

There was already a database check constraint allowing only Profile primary key
1. No duplicate profile model or singleton framework was needed. The repository
had one profile and one unpublished, file-free resume draft. These records and
all other original content were retained.

## Editor and data flow

`/dashboard/profile/` directly opens the owner form, with no profile list, add,
or delete screens. Fields are prefilled and grouped into Basic information, Hero,
About, Contact and social links, Profile image, Availability and labels, and Resume.
There are field errors, an error summary, Save Changes, discard, and success feedback.
The sidebar highlights Profile / About and reuses the existing mobile drawer.
Overview profile actions now open the custom editor.

Saving writes to the existing Profile and current Resume in one database
transaction after both forms validate. A blank new resume section creates no
record. The editor selects the same first published resume as SiteView, or the
first draft when none is public. Existing additional resumes are not deleted or
implicitly published; they remain manageable in Django Admin.

`/api/v1/portfolio/site/` reads the same models on every request. Uploaded photos
are serialized as the existing `avatar_url` API property, preserving the client
contract. Resume `file_url` continues to come from the existing serializer.
React fetches on load, manual refresh, and return to a focused/visible tab.
Content edits require no frontend rebuild. This is refresh-on-return behavior,
not server-pushed updates while a visitor stays continuously on the tab.

Public layout is preserved. About now handles browser CRLF paragraph separators
and omits empty paragraphs. Static metadata is generic until the API supplies the
name and bio; search indexing remains disabled. A disconnected frontend shows
an unavailable state instead of an obsolete personal snapshot.

## Models, migrations, and uploads

- `portfolio.0002_profile_avatar`: adds one blank ImageField using existing media
  storage at `profiles/%Y/%m/`. Existing avatar URLs remain usable.
- `resume.0002_alter_resume_file`: records the new PDF-content validator; no new
  resume table, ownership model, or document library.
- Pillow is the only new dependency (`Pillow>=12.0,<13.0`; installed version 12.3.0).
- Both migrations are applied to the local database. All pre-existing column
  values and rows across eight content tables were compared before/after and
  matched. Browser mutations ran in a separate SQLite copy and media directory.

Photos accept JPEG, PNG, and WebP only, verified through Pillow with extension,
5 MB, 20-megapixel, and decompression-bomb checks. The form shows the current
photo and a local preview of a selected upload. PDFs require a `.pdf` extension,
5 MB maximum, PDF header, and end marker. This is signature validation, not a
full PDF parser or malware scanner.

No new selection preserves the current file. Replacement uses a new storage
filename, so it does not overwrite old cached/shared files. Old files are retained;
this task does not introduce media cleanup. Clearing the uploaded photo exposes
the optional external URL; clearing both restores initials. An unpublished
resume is omitted from the public API. A published resume without a PDF retains
the existing print action. Media remains public when its URL is known; unpublishing
a record does not revoke an already-known file URL. Production Caddy's existing
attachment/nosniff media policy is unchanged.

## Authorization and security

- Active authenticated staff plus `portfolio.change_profile` for existing data;
  `portfolio.add_profile` for initial setup. GET never creates a record.
- Resume editing separately requires `resume.change_resume` or `resume.add_resume`.
  Unauthorized resume controls are omitted and forged resume submissions get 403.
- All writes use CSRF-protected POST requests. Private responses are not cached.
- Model/form validation enforces required fields, length limits, email syntax,
  and HTTP/HTTPS social/photo URLs. Plain-text content is escaped by Django/React.
- Upload extensions/content/size are checked server-side; arbitrary executable
  file types are rejected. Files use existing Django storage, not user paths.
- Public API fields remain explicitly allowlisted and read-only. Raw storage
  objects, internal permissions, and backend settings are not serialized.
- Existing database singleton constraint and Admin add protection are retained.

## Relevant files changed

New:

- `apps/dashboard/profile_forms.py`
- `apps/dashboard/profile_views.py`
- `apps/dashboard/templates/dashboard/profile/form.html`
- `apps/dashboard/static/dashboard/profile.css`
- `apps/dashboard/static/dashboard/profile.js`
- `apps/dashboard/tests/test_profile.py`
- `apps/portfolio/migrations/0002_profile_avatar.py`
- `apps/resume/migrations/0002_alter_resume_file.py`
- `docs/TASK6_PROFILE_HANDOFF.md`

Updated:

- `apps/dashboard/urls.py`, `overview.py`, and shell/home templates.
- `apps/core/validators.py`.
- `apps/portfolio/models.py`, `serializers.py`, and `views.py`.
- `apps/resume/models.py` and `requirements.txt`.
- `frontend/lib/portfolio.ts`, `app/page.tsx`, `app/layout.tsx`, and
  `components/portfolio-panels.tsx`.
- `frontend/.env.example`, `frontend/README.md`, `README.md`,
  `deploy/Dockerfile.web`, `deploy/README.md`, and `docs/DASHBOARD_HANDOFF.md`.
- Removed `frontend/data/portfolio.json` and runtime personal fallback imports.

Pre-existing Skills/history work and their uncommitted files remain in the tree.

## Automated verification

| Command | Result |
| --- | --- |
| `.venv\Scripts\python.exe manage.py test` before changes | 172 tests passed |
| `.venv\Scripts\python.exe manage.py test apps.dashboard.tests.test_profile` | 29 tests passed |
| `.venv\Scripts\python.exe manage.py test` after changes | 201 tests passed in 19.428 seconds |
| `.venv\Scripts\python.exe manage.py check` | No issues |
| `.venv\Scripts\python.exe manage.py makemigrations --check --dry-run` | No changes detected |
| `npm run typecheck` in frontend | Passed |
| `npm run lint` in frontend | Passed |
| `npm run build` in frontend | Passed, static export completed |
| `frontend\node_modules\.bin\oxlint.cmd apps/dashboard/static/dashboard/profile.js` | Passed |
| `git diff --check` | Passed |

There is no configured backend linter. The build emitted non-failing Node glob
experimental/plugin timing notices. No Docker runtime or production deployment
test was performed. A search of the final client output found no old personal
snapshot strings (`Anil GC`, `Building Portfolio OS`, `Kathmandu, Nepal`).

The new tests cover anonymous/nonstaff/inactive/permissionless access, view-only
and add-only limitations, resume permissions, CSRF, initial singleton setup,
database duplicate rejection, validation, escaped text, public profile updates,
optional clearing, image formats/size/pixel limits, filename-safe replacement,
file preservation, PDF validation/replacement, draft isolation, and API read-only
behavior. The first test run exposed open file handles on Windows; validators
now close files they open while preserving uploaded-file streams.

## Browser verification

Chromium, with the production frontend build at 5176 and isolated Django at 8006:

- Changed name, professional headline, hero heading, About, and GitHub URL;
  saved and verified values in the public UI.
- Selected photo preview, uploaded photo rendering, replacement URL change,
  and image decoding verified.
- Uploaded and replaced a PDF; verified new URL, HTTP 200/PDF content, and the
  actual Open PDF action opening the replacement document.
- Returned to the public tab with a focus event and verified fresh API values
  without rebuilding/reloading that page.
- Checked editor and public About at 1440, 1024, 768, 390, and 320px: no horizontal
  document overflow. Visually inspected desktop/editor and mobile/public captures.
- Mobile navigation opens, Escape closes it, and focus returns to its trigger.
- Invalid social URL shows validation feedback; optional About/social/photo
  clearing and resume unpublishing work. Public initials, hidden social links,
  and resume empty state replace absent content without broken links.
- Verified separate About paragraphs after a real form submission.
- Simulated API failure on a fresh load: unavailable UI with no stale owner
  snapshot; restored connection successfully.

Scripts, screenshots, authentication state, and test databases are under ignored
`output/playwright/`. Do not publish those artifacts. An existing `/favicon.ico`
404 occurred in the initial public browser session; it is unrelated to Task 6.
These checks do not claim physical-device or cross-browser coverage.

The isolated QA servers were stopped after verification. The normal portfolio
Django process at port 8000 was still running older code with `--noreload`; it was
verified by its executable/command line and restarted with auto-reload enabled.
The new Profile route now redirects anonymous visitors to login, and the normal
frontend at 5173 reads the original owner's unchanged content from Django.

## Next task — not started

Task 7 should add a permission-protected Contact Messages list and detail view,
search plus read/unread filtering, and explicit mark-read/mark-unread actions.
Reuse the existing Message model and keep email/body details out of overview
cards. Leave outbound replies, bulk actions, Media Library, Settings, and analytics
expansion for later scope.
