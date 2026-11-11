# Spatial query performance

`GET /branches/nearby` runs one PostGIS query: an `ST_DWithin` radius filter on
`Branches.location` (a generated `geography(Point, 4326)` column), ordered by
`ST_Distance`, then paginated. `Branches.location` has a GiST index
(`ix_branches_location`).

## How it was measured

`scripts/benchmark_nearby.py` does the following:

1. It builds a throwaway `<dev>_benchmark` database from the Alembic migrations.
2. It seeds synthetic branches spread uniformly over Saudi Arabia (lat 16–32, lng 36–56), with a fixed seed.
3. It runs `VACUUM ANALYZE`.
4. It runs `EXPLAIN (ANALYZE, BUFFERS)` on the exact SQL that `nearby_branches_query()` produces for the API.

The no-index variant drops the index inside a transaction and rolls it back. Both
variants therefore run against identical data, on a warm cache, and the reported
time is the median of 15 runs.

```powershell
.\.venv\Scripts\python.exe -m scripts.benchmark_nearby --branches 100000 --radius-km 5
```

## Results

PostgreSQL 18.6 and PostGIS 3.7.0 on Windows 11, on a development laptop.
Search origin: Dhahran. Page size: 20.

| Branches | Radius | Rows returned | With GiST index | Without index | Plan without index |
|---:|---:|---:|---:|---:|---|
| 1,000 | 5 km | 0 | 0.06 ms | 4.1 ms | Seq Scan |
| 10,000 | 5 km | 0 | 0.09 ms | 36.2 ms | Seq Scan |
| 100,000 | 5 km | 3 | 0.21 ms | 323.8 ms | Parallel Seq Scan |
| 100,000 | 50 km | 20 (of 188) | 5.2 ms | 322.4 ms | Parallel Seq Scan |

With the index, the planner uses `Index Scan using ix_branches_location` for small
result sets and a `Bitmap Index Scan` for larger radii. The index condition is
`location && _st_expand(origin, radius)`, a cheap bounding-box check, followed by
an exact `st_dwithin` recheck on the few candidates it returns. In the 100k / 5 km
case the indexed plan reads 9 shared buffers; the sequential scan reads 2,462 and
computes a spheroidal distance for every branch.

## Caveats

- The data is synthetic and uniformly distributed. Real branches cluster in cities, so
  a city-centre search with a large radius returns more candidates and costs more than
  the uniform numbers suggest. The 50 km row gives a rough idea of that case.
- The times are execution time on a warm cache on one machine. They exclude network and
  ORM overhead and say nothing about concurrent load.
- Below roughly 1,000 branches, both plans finish in a few milliseconds. The index only
  matters at larger sizes.
- The marketplace eligibility check (`ST_DWithin` between an order's pickup point and a
  branch's service area) uses the partial GiST index `ix_orders_marketplace_pickup`. It
  has not been benchmarked separately.
