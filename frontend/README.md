# Ghasel frontend

A dependency-free single-page app: plain HTML, CSS and native ES modules. There is no
build step. Every number, status, distance and rating it shows comes from the Ghasel API.

## Running it

Start the API from the repository root, then serve this folder:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
.\.venv\Scripts\python.exe -m http.server 5500 --directory .\frontend
```

Open http://127.0.0.1:5500. The API origin defaults to `http://127.0.0.1:8000`; to use
another, define `window.GHASEL_API_BASE` before `js/main.js` loads. The API's CORS policy
allows `http://127.0.0.1:5500` and `http://localhost:5500`.

## Structure

```
index.html            App shell: sidebar / mobile top bar, page outlet, modal and toast roots
styles/
  base.css            Design tokens (colours, radii, shadows), reset, typography
  layout.css          Auth screen, app shell, navigation, grids, breakpoints
  components.css      Buttons, forms, cards, badges, ratings, order tracking, modals, states
js/
  main.js             Boot: restore the session, choose the role's pages
  router.js           Hash routing and navigation
  api.js              The only module that talks to the backend
  session.js          Token persistence
  dom.js              html`` templates that escape every interpolated value
  feedback.js         Toasts, modals, confirm dialog, loading/empty/error states
  format.js           Dates, distances, status badges, star ratings
  lifecycle.js        Display labels for order statuses (the rules live in the API)
  location.js         Geolocation, city presets, saved search location
  icons.js            Inline SVG icons
  components/         Order cards & dialogs, branch cards & details, location picker, branch form
  pages/              One module per screen
```

## What each role sees

| Role | Screens |
|---|---|
| Customer | Home, nearby discovery (distance and rating), marketplace or direct requests, order tracking timeline, reviews, profile |
| Branch manager | Available orders nearest first, accept, advance each stage, cancel before pickup, branch details and location |
| Laundry owner | Application status, branches (with location and service radius), branch managers |
| Admin | Approve laundry applications, list accounts |

## Notes

- **Location.** Customers can share their browser location, pick a city centre, or type
  coordinates. There is no paid map or geocoding service.
- **Tracking.** Progress is the order's recorded status history. Nothing is simulated,
  and there is no live GPS.
- **Security.** All dynamic text is escaped by the `html` template tag. The access token
  is kept in `localStorage`, which is acceptable for this local project but means any XSS
  could read it.
