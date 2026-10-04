# Ghasel Frontend

A deliberately small vanilla HTML/CSS/JS frontend matched to the current Ghasel FastAPI API.

## Run it locally

From the repository root, start the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

In a second terminal, serve this folder:

```powershell
.\.venv\Scripts\python.exe -m http.server 5500 --directory .\frontend
```

Open `http://127.0.0.1:5500`. The API base defaults to `http://127.0.0.1:8000`; `window.GHASEL_API_BASE` can override it. FastAPI allows the frontend origins `http://127.0.0.1:5500` and `http://localhost:5500` for local development.

## Current API assumptions

This UI uses the current backend routes:
- POST `/auth/register`
- POST `/auth/login`
- GET/PATCH `/users/me`
- GET `/users/` (admin)
- POST `/laundries/`
- GET `/laundries/requests` (admin)
- POST `/laundries/requests/{request_id}/approve` (admin)
- GET `/laundries/{laundry_id}`
- GET/POST `/laundries/{laundry_id}/branches`
- POST `/laundries/{laundry_id}/managers`
- POST `/orders/` with a branch ID for direct orders or `null` for open orders
- GET `/orders/` returns orders scoped by customer, manager branch/open pool, or admin role
- GET `/orders/{order_id}`
- PATCH `/orders/{order_id}/status`

## Known backend gaps reflected honestly in the UI

- `GET /laundries/` (nearby laundries) is currently unimplemented, so V1 uses laundry-ID lookup.
- Open orders are currently visible to all managers; nearby filtering and notifications are deferred.
- Ratings, ETA, maps, reviews and real nearby search are intentionally not faked; they can appear in V2 when the API supports them.
