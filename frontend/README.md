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

Run `npm run typecheck`, `npm run lint`, and `npm run build` before publishing.
The lint configuration excludes generated, unmodified UI primitives and their
mobile hook. They remain in the TypeScript compilation.
