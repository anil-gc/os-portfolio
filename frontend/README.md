# Portfolio React Client

Run `npm ci` and `npm run dev`; the site opens at port 5173. Django must run at port
8000 for live content and message submission. Vite proxies `/api` and `/media`.

The client uses React, TypeScript, Vinext/Vite, Lucide, and generated Base UI/Shadcn
primitives. `app/page.tsx` owns the desktop shell; `components/portfolio-panels.tsx`
contains content views. Data and URL helpers are in `lib/portfolio.ts`.

`npm run build` exports static assets to `dist/client`. Serve them under the same
origin as Django using the parent repository's Caddy configuration. `npm start`
previews the static output locally; it is not a production application server.

`VITE_API_BASE_URL` is a build-time public API base. Portfolio content always comes
from Django. Loading and unavailable states replace the old bundled personal
snapshot; `VITE_ALLOW_DEMO_FALLBACK` is no longer used. `data/demo.json` is an
optional backend seed fixture and a type-only import, never runtime content.
Search indexing remains disabled until the site is ready for public launch.

For the existing Vercel frontend and Render backend, set Vercel's production
`VITE_API_BASE_URL` to `https://os-portfolio-api.onrender.com/api/v1` before
building. On Render, set `DJANGO_CORS_ALLOWED_ORIGINS` to the exact public frontend
origin (`https://os-portfolio-o54c.vercel.app`, without a trailing slash).
The API allows cross-origin requests only from configured origins and does not
enable cross-origin session cookies. Keep Django admin on its Render origin;
its CSRF protection is separate and remains enabled.

The public API also needs a real Profile record (ID 1), entered through the
authenticated Django admin/dashboard. A missing profile returns 404 and displays
the frontend's unavailable screen. Do not automatically seed demo content into
an existing production database. The backend root `/` has no route; use
`/api/v1/core/health/` for process liveness and `/api/v1/projects/` for a database
read check. Neither check alone establishes that portfolio content is complete.

Run `npm run typecheck`, `npm run lint`, and `npm run build` before publishing.
The lint configuration excludes generated, unmodified UI primitives and their
mobile hook. They remain in the TypeScript compilation.
