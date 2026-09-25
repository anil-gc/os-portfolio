# Dashboard handoff — Task 7

Task 7 is complete. Read [the Contact Messages handoff](TASK7_MESSAGES_HANDOFF.md)
for the contact flow, routes, permissions, 233-test result, browser verification,
and proposed next scope. No subsequent task has started.

The [Task 6 Profile / About handoff](TASK6_PROFILE_HANDOFF.md) retains the previous
profile, upload, migration, and 201-test checkpoint. Its next-task recommendation
has now been completed.

## Task 5 historical handoff

Verified on September 25, 2026. The following records the Task 5 checkpoint.
Existing uncommitted Task 4 work was preserved. This handoff does not indicate
a GitHub push or production deployment.

## Completed scope

Experience, Education, and Certificates can be listed, created, edited, and
deleted in the custom Django dashboard. Lists have search, publication filters,
10-entry pagination, display ordering, status badges, and empty states. Forms
show field errors and save feedback; deletion has an explicit confirmation page.
The sidebar includes all three sections and highlights the active section.

## Existing architecture and reuse

All three sections already had Django models, serializers, public list APIs,
and React presentation components. The combined portfolio API reads those same
models. Static JSON is only an optional disconnected-preview fallback.

The implementation uses those existing models and their `sort_order` and
`is_published` fields. No models, migrations, dependencies, uploads, or storage
systems were added. Certificates have an optional credential URL, not an image
field or credential-ID field. Experience and Education store full dates; a blank
end date means Present. Existing model validation rejects reversed date ranges.

DashboardAccessMixin, the authenticated shell, field partials, publishing toggle,
alerts, empty states, buttons, and responsive Projects styles are reused.
Each domain keeps its own form and routes; small shared view/template helpers
cover the common behavior without introducing a general CRUD framework.

## Routes

| Section | List | Create | Edit | Delete confirmation |
| --- | --- | --- | --- | --- |
| Experience | `/dashboard/experience/` | `/dashboard/experience/new/` | `/dashboard/experience/<id>/edit/` | `/dashboard/experience/<id>/delete/` |
| Education | `/dashboard/education/` | `/dashboard/education/new/` | `/dashboard/education/<id>/edit/` | `/dashboard/education/<id>/delete/` |
| Certificates | `/dashboard/certificates/` | `/dashboard/certificates/new/` | `/dashboard/certificates/<id>/edit/` | `/dashboard/certificates/<id>/delete/` |

## Security and public integration

Every management route requires active staff access and the relevant model
permission. Lists accept view or change permission; writes require add, change,
or delete permission. Private responses are not cached. Mutations require
CSRF-protected POST requests; GET only displays delete confirmation.

Published entries feed both the section list API and `/api/v1/portfolio/site/`.
Drafts remain private. The existing public UI refreshes on page load, manual
refresh, and return to a visible/focused tab. No frontend rebuild is needed for
content edits. A disconnected static preview cannot synchronize with Django.
Django Admin remains available as a fallback.

## Relevant files

- `apps/dashboard/history_forms.py` — domain forms and date/URL/order validation.
- `apps/dashboard/history_views.py` — shared list/save/delete behavior and domain views.
- `apps/dashboard/templates/dashboard/history/` — base, list, form, and delete templates.
- `apps/dashboard/static/dashboard/history.css` — history cards and responsive details.
- `apps/dashboard/tests/test_history.py` — 70 tests across the three modules.
- `apps/dashboard/urls.py` — all 12 management routes.
- `apps/dashboard/overview.py` — custom management links.
- `apps/dashboard/templates/dashboard/{shell,home}.html` — navigation and overview copy.
- `apps/dashboard/templates/dashboard/partials/icon.html` — Education icon.
- `README.md`, `deploy/README.md`, and this file — workflow and handoff documentation.
- `.gitignore` — exclude generated Playwright snapshots alongside existing QA artifacts.

The working tree also contains the earlier Task 4 Skills forms, views, templates,
styles, and tests. Those files were retained, not rewritten.

## Verification

- `manage.py test`: 172 tests passed, including 70 Task 5 tests.
- `manage.py check`: no issues.
- `manage.py makemigrations --check --dry-run`: no changes detected.
- Frontend `npm run typecheck`, `npm run lint`, and `npm run build`: passed.
- No backend lint configuration is present.
- Browser: Experience create → public display → edit → public update → confirmed
  delete → public removal passed, including invalid dates and current/past state.
- Browser: Education completed the same lifecycle, including changing an end
  date to Present and displaying the update publicly.
- Browser: Certificates completed the same lifecycle, including invalid URL
  rejection and replacement of the publicly displayed credential link.
- Lists checked at 320, 390, 768, 1024, and 1440px without horizontal overflow.
  Mobile forms and delete confirmations fit. Empty states checked at 320, 768,
  and 1440px. Mobile navigation opens, Escape closes it, and focus returns.
- Browser public refresh was triggered with a simulated focus event. These are
  Chromium checks, not physical-device or cross-browser certification.
- Browser mutations used an isolated SQLite copy. The original database's SHA-256
  hash remained unchanged; its 2 experience, 1 education, and 3 certificate
  records were preserved.

Screenshots and local QA scripts are in ignored `output/playwright/`.
The existing public `/favicon.ico` 404 remains unrelated to Task 5.
Docker deployment runtime was not checked in this task.

## Task 5's original next-step recommendation — now completed

Task 6 should add one permission-protected Profile/About editing page using the
existing singleton Profile model, current fields, and dashboard form patterns.
Cover validation and public API refresh, retain Django Admin, and keep Contact
Messages, Media Management, and Settings outside that scope.
