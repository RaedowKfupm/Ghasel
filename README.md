# Ghasel

A laundry marketplace. Customers post a pickup request and nearby laundry branches
compete to accept it, or the customer picks a rated branch directly. The customer then
follows the order through each cleaning stage, and rates it once it is delivered.

FastAPI · PostgreSQL + PostGIS · SQLAlchemy 2 · Alembic · Pydantic 2 · pytest · vanilla ES-module frontend

| Nearby discovery | Order tracking |
|---|---|
| ![Nearby discovery](docs/screenshots/nearby-discovery.png) | ![Order tracking](docs/screenshots/order-tracking.png) |
| **Branch operations** | **Customer home** |
| ![Branch operations](docs/screenshots/branch-operations.png) | ![Customer home](docs/screenshots/customer-home.png) |

<sub>The screenshots use the demo dataset from `scripts/seed_demo.py`.</sub>

## Features

- **Marketplace ordering.** A customer posts an order without choosing a branch. It is
  offered only to branches whose service radius covers the pickup point. The first branch
  to accept wins, and that is enforced atomically in PostgreSQL. Customers can also
  request a specific branch directly.
- **Nearby discovery.** Branches inside a radius, nearest first, with the distance in
  kilometres. This uses PostGIS `ST_DWithin` / `ST_Distance` on a GiST-indexed
  `geography` column.
- **Order tracking.**
  - Stages: `pending → accepted → picked_up → cleaning → ready → delivering → completed`.
  - Customers can cancel before pickup.
  - Each change is recorded, with its time and who made it, in an append-only history
    that drives the timeline in the UI.
- **Verified reviews.** Only the customer of a completed order can review it, once.
  Branch ratings are averaged from those reviews.
- **Roles.**
  - Customers place and track orders.
  - Laundry owners apply for approval and run branches and managers.
  - Branch managers work their branch's order queue.
  - Admins approve laundry applications.

## Architecture

```
routes/      thin FastAPI handlers: parse input, pick the dependency, call one service
services/    business rules and transactions (orders, branches, reviews, laundry, users, auth)
core/        settings, auth dependencies, domain errors, enums, the order state machine
models/      SQLAlchemy models          schemas/   Pydantic request/response models
db/          engine/session, PostGIS helpers
alembic/     migration history (the schema's source of truth)
frontend/    static SPA: api client, components, one module per page
```

- **Routes stay thin.** Ownership and state rules live in services, so no alternative
  call path can skip them. Services raise domain errors (`NotFoundError`, `ConflictError`,
  ...), and a single handler maps those to HTTP responses.
- **One state machine.** `app/core/order_lifecycle.py` is a pure table of transitions,
  the roles allowed to make each one, and the timestamp each sets. The API exposes each
  order's `next_status`, so the UI never reimplements the rules.

### Key design decisions

**Atomic acceptance without application-level locking.** Every status change is a single
compare-and-set:

```sql
UPDATE orders SET status = 'ACCEPTED', branch_id = :branch, accepted_at = now()
WHERE id = :id AND status = 'PENDING'
  AND (branch_id = :branch OR (branch_id IS NULL AND ST_DWithin(pickup_location, <branch location>, <radius>)))
RETURNING id
```

PostgreSQL locks the row for the first writer. Concurrent writers wait, then re-evaluate
the `WHERE` clause after it commits, so exactly one succeeds and the others get `409`.
The eligibility check sits inside the statement, so a stale read cannot accept an order
the branch is no longer allowed to take. The status-history row is inserted in the same
transaction. Tests run 12 threads against one order, plus a deterministic interleaving
where a blocked request must lose.

**Coordinates as source of truth, geography as a generated column.** Latitude and
longitude are validated by `CHECK` constraints. A `STORED` generated
`geography(Point, 4326)` column derives from them, so the two cannot disagree, and it
carries the GiST index.

**Reviews reference only the order.** The branch and customer are read through the order,
so they cannot drift. A unique `order_id` allows one review per order, even under
concurrent submissions.

**Measured spatial performance.** With 100,000 branches, a 5 km nearby search takes
0.21 ms with the GiST index and 324 ms without it (an index scan versus a parallel
sequential scan). Methodology, plans and caveats are in
[docs/performance.md](docs/performance.md).

## Getting started

Prerequisites: Python 3.12+ and PostgreSQL 15+ with the **PostGIS 3** extension
installed. On Windows: Stack Builder → Spatial Extensions → PostGIS.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env            # then fill in DATABASE_URL and SECRET_KEY
.\.venv\Scripts\alembic upgrade head
```

A database created by the old `create_tables.py` script should first be stamped with
`alembic stamp 0001`, then upgraded. The migrations preserve existing rows.

Run the API and the frontend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload            # http://127.0.0.1:8000/docs
.\.venv\Scripts\python.exe -m http.server 5500 --directory .\frontend  # http://127.0.0.1:5500
```

### Demo data

`python -m scripts.seed_demo` builds a separate `<dev database>_demo` database with
sample companies, branches around Dhahran, Al Khobar and Dammam, orders in every stage,
and reviews. It never touches your development database. Every order is driven through
the real service layer. To use it, point `DATABASE_URL` at the demo database and sign in
with `sara@ghasel.demo`, `dana@ghasel.demo` (manager), `hassan@ghasel.demo` (owner) or
`admin@ghasel.demo`. The password is `demo-password`.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff check app tests scripts alembic
```

The suite creates a throwaway `<dev database>_test` database, built from the Alembic
migrations. You can set `TEST_DATABASE_URL` to use a different one. The suite refuses to
run against any database whose name doesn't contain "test". It covers:

- authentication and role guards, and resource ownership (orders, branches, companies);
- every lifecycle edge, rejected transitions and the cancellation cutoff;
- concurrent acceptance and concurrent duplicate reviews;
- radius boundaries (inclusive), distance ordering, pagination, and invalid or non-finite
  coordinates;
- review eligibility, uniqueness and rating aggregation;
- database `CHECK` and unique constraints;
- a migration round trip (upgrade, downgrade to base, upgrade) compared against the models.

## API overview

| Endpoint | Who | Purpose |
|---|---|---|
| `POST /auth/register`, `POST /auth/login` | public | JWT sign-up and sign-in (customer or laundry owner) |
| `GET/PATCH /users/me` | any user | Profile |
| `GET /branches/nearby?latitude&longitude&radius_km` | public | Branches by distance, with ratings |
| `GET /branches/{id}`, `GET /branches/{id}/reviews` | public | Branch details and reviews |
| `PATCH /branches/{id}` | owner, branch manager | Edit details, location and service radius |
| `POST /orders/` | customer | Marketplace (no `branch_id`) or direct order |
| `GET /orders/`, `GET /orders/{id}` | customer, manager, admin | Scoped to what the caller may see; details include history |
| `GET /orders/available` | manager | Orders the branch may accept, nearest pickup first |
| `POST /orders/{id}/accept`, `/cancel`; `PATCH /orders/{id}/status` | manager / customer | Lifecycle actions |
| `POST /orders/{id}/review` | customer | Review a completed order |
| `POST /laundries/`, `GET /laundries/requests/me` | owner | Apply and check application status |
| `POST /laundries/{id}/branches`, `/managers` | owner | Add branches and managers |
| `GET /laundries/requests`, `POST .../approve` | admin | Review applications |

Interactive documentation is served at `/docs`.

## Known limitations

- No live GPS tracking: progress is what the laundry records.
- No geocoding: locations come from the browser, a city preset or typed coordinates.
- No notifications, payments, refresh tokens or rate limiting yet.
- The access token is stored in `localStorage`.
