# Portfolio React Client

Run `npm ci` and `npm run dev`; the site opens at port 5173. Django must run at port
8000 for live content and message submission. Vite proxies `/api` and `/media`.

The client uses React, TypeScript, Vinext/Vite, Lucide, and generated Base UI/Shadcn
primitives. `app/page.tsx` owns the desktop shell; `components/portfolio-panels.tsx`
contains content views. Data and URL helpers are in `lib/portfolio.ts`.

`npm run build` exports static assets to `dist/client`. Serve them under the same
origin as Django using the parent repository's Caddy configuration. `npm start`
previews the static output locally; it is not a production application server.

`VITE_API_BASE_URL` is a build-time public API base. `VITE_ALLOW_DEMO_FALLBACK=true`
permits a standalone preview of `data/portfolio.json`. Live deployments should set it to false.
The standalone preview cannot send messages or edit Django data while disconnected.
The original fictional seed fixture is separate from the personalized snapshot. Search indexing is
disabled until the profile and static metadata are ready for public launch.

Run `npm run typecheck`, `npm run lint`, and `npm run build` before publishing.
The lint configuration excludes generated, unmodified UI primitives and their
mobile hook. They remain in the TypeScript compilation.
