# HomeChef

A responsive demo homepage with React, Node.js, and Express. The frontend is bundled with esbuild, without using Vite for the application build.

## Run

- `pnpm install`
- `pnpm build`
- `pnpm start` serves the React frontend and Express API on port 4173.

## Structure

- `frontend/components`: reusable meal, cook, and accessible dialog components
- `frontend/lib`: pure meal filtering and sorting
- `backend/routes`: Express API routes (`/api/catalog`, `/api/health`)
- `backend/repositories`: data access boundary for a later Supabase/PostgreSQL HTTP adapter
- `backend/data`: sample listings and cooks
- `backend/server.js`: standard Node.js/Express entrypoint
- `backend/worker.js`: Sites hosting adapter for the same Express app

## Demo boundaries

Eight sample meal listings across Warsaw, Kraków, and Wrocław, priced in Polish złoty. Calendar dates and hourly pickup choices (8 AM to 10 PM) filter against mock listing availability. Search, area and pickup-time selection, filters, sorting, kitchen browsing, and device-local favourites are functional. Accounts, registrations, orders, payments, and pickup booking are not yet implemented. No real cook identity or availability is claimed. Images were extracted from the user-supplied visual reference and are demo assets. The supplied reference imagery is illustrative and should be replaced with accurate meal photos before real listings.

Next modules can add partner registration, assisted NGO onboarding, first listing creation, ordering, reviews, mock payments, and scheduling. Store real data through the repository layer; do not treat browser favourites as a customer database.

## Address search and pages

`/api/locations?q=...` performs explicit Polish street/city/postcode lookup through Nominatim. The location dialog includes OpenStreetMap attribution, errors, empty results, and cancellation. Results are restricted to Poland. A bounded in-memory cache and request throttle suit this private low-volume demo; switch the provider in `backend/services/locationSearch.js` before a high-volume release. Kitchen coordinates are approximate mock positions. Meals are matched within a 15 km straight-line radius, with no invented listings for unsupported areas.

Pickup date/time are optional and can be cleared independently of the area. Dedicated `/how-it-works`, `/our-mission`, and `/become-a-cook` pages use minimal existing copy pending the user's UI designs. Each has built HTML for direct navigation and refresh.
