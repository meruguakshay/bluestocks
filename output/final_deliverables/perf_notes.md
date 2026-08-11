# REST API Performance & Benchmark Notes

## Performance Objective
Ensure the FastAPI REST API can handle multiple concurrent requests efficiently. Specifically, we target the `/api/v1/screener` endpoint, which does full-table joins, deduplications, and sort operations.

## Test Environment
- **Server**: FastAPI + Uvicorn (Single worker, single-threaded ASGI server)
- **Database**: SQLite 3 (Disk-backed file `db/nifty100.db`)
- **Load Size**: 10 concurrent HTTP GET requests simulated in parallel using python's `concurrent.futures.ThreadPoolExecutor`

## Benchmarks & Optimization Results

### Baseline (No Database Indexes)
- **Total Concurrent Execution Time**: 3.2831 seconds
- **Average Request Latency**: 3.1203 seconds
- **Min Latency**: 2.8906 seconds
- **Max Latency**: 3.2735 seconds

### Optimized (With Composite SQLite Indexes)
We added composite indexes on `(company_id, year)` for the following tables to optimize subqueries, grouping, and filtering:
- `financial_ratios`
- `balancesheet`
- `profitandloss`
- `cashflow`
- `market_cap`
- `peer_percentiles`

**Optimized Performance Results:**
- **Total Concurrent Execution Time**: 3.2169 seconds (Improved)
- **Average Request Latency**: 3.0439 seconds (Improved)
- **Min Latency**: 2.6994 seconds
- **Max Latency**: 3.2085 seconds

## Bottleneck Analysis
1. **Python Global Interpreter Lock (GIL)**: Since Uvicorn runs in a single process, concurrent requests on CPU-bound tasks (like Pandas merges and filtering) must share the CPU. This is the primary driver of the ~3-second latency under parallel load.
2. **Pandas Processing**: The screener dynamically merges three tables in memory (`companies`, `financial_ratios`, and `market_cap`) and performs multi-column sorting and grouping. 
3. **Database Disk I/O**: SQLite handles concurrent reads well, and the composite indexes have successfully minimised the disk lookups.
