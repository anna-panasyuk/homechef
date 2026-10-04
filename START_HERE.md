# HomeChef source code

This archive contains the complete source checkout for the website published on 3 October 2026, including the hero banner, larger H2 messages, seller profile photos, chef stories directly below search, About the cook sections, and the impact carousel.

## Run locally

Install Node.js 22.13 or newer. Extract the ZIP, open a terminal in the homechef folder, and run:

```bash
npm install
npm run build
npm start
```

Open http://localhost:4173 in your browser manually; npm start does not open it automatically. Keep the terminal open while using the site. Run each command above separately. Press Ctrl+C to stop the server. To use a different port, set the PORT environment variable before running npm start. After changing frontend code, run npm run build again and refresh the browser.

The project also includes pnpm-lock.yaml if you prefer pnpm and reproducible dependency resolution.

## Application files

- frontend/: React pages, components, CSS, search, calendar, filters, and favourites
- backend/: Express API, mock listings, repositories, address lookup, and server entrypoints
- shared/: date/time helpers shared by the frontend and backend
- public/: meal/cook images, image source references, and favicon
- scripts/build-homechef.mjs: esbuild production build (the active app does not use Vite)
- .openai/hosting.json: configuration for the existing hosted Site
- README.md: architecture and demo details

## Included features

Street, postcode, and city lookup in Poland; optional calendar date and hourly pickup selection from 8 AM to 10 PM; coordinate-based nearby meal search; cuisine search; filters; sorting; local favourites; and separate How it works, Our mission, and Become a cook pages.

## Current boundaries

Meal listings, kitchen coordinates, prices, and reviews are sample data. Listings currently exist near Warsaw, Kraków, and Wrocław. Address lookup uses the public Nominatim service and needs an internet connection. Favourites are saved only on the current browser/device. Accounts, real orders, partner registration, payments, and a database are not implemented yet. The frontend loads DM Sans from Google Fonts with a system-font fallback.

## Starter files

The complete checkout also includes unused starter files in app/, components/, build/, examples/, db/, and related framework configuration. They are retained for an exact source export. The currently published application is built only from frontend/, backend/, shared/, and public/ using scripts/build-homechef.mjs; app/page.tsx is not the homepage in use.

No node_modules, compiled output, Git history, source credentials, or local environment files are included.
