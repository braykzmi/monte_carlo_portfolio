# Dockerized Portfolio Monte Carlo Simulator

FastAPI backend (Bloomberg-enabled with DEMO fallback) + React/Vite frontend, fully Dockerized with `dev` and `prod` profiles. Supports ticker search, calibration from historicals, and Monte Carlo simulation (correlated GBM with optional Student-t heavy tails). Ships with a Postman collection.

---

## Table of Contents

* [Features](#features)
* [Architecture](#architecture)
* [Repository Layout](#repository-layout)
* [Prerequisites](#prerequisites)
* [Quick Start](#quick-start)

  * [Dev (hot reload)](#dev-hot-reload)
  * [Prod (static frontend + multi-worker backend)](#prod-static-frontend--multi-worker-backend)
  * [Run without Docker (Desktop API users)](#run-without-docker-desktop-api-users)
* [Environment Variables](#environment-variables)

  * [Back end](#back-end)
  * [Front end](#front-end)
  * [Bloomberg Connectivity Scenarios](#bloomberg-connectivity-scenarios)
* [API Reference](#api-reference)
* [Simulation Model](#simulation-model)
* [Frontend Usage](#frontend-usage)
* [Troubleshooting](#troubleshooting)
* [Acceptance Criteria](#acceptance-criteria)
* [Limitations & Non-Goals](#limitations--non-goals)
* [Roadmap (nice-to-haves)](#roadmap-nice-to-haves)
* [Postman Collection](#postman-collection)
* [Changelog](#changelog)
* [License](#license)

---

## Features

* **Docker-first**: separate images for backend and frontend; compose profiles for dev/prod.
* **Bloomberg integration**:

  * **SERVER (B-PIPE)** mode for containers.
  * **DESKTOP** (best-effort) mode; recommended to run backend on host.
* **DEMO mode**: fully functional without Bloomberg entitlements.
* **Calibration**: pulls PX\_LAST or TR index, cleans, computes annualized μ/σ and correlation.
* **Simulation**: correlated GBM; optional Student-t elliptical scaling; VaR & ES stats.
* **Charts**: all path lines (capped to 500) and final PnL histogram.
* **Robustness**: diagonal loading on Cholesky; strict shape checks with actionable errors.

---

## Architecture

* **Backend**: FastAPI (`/backend`)

  * Endpoints: `/api/search`, `/api/calibrate`, `/api/simulate`
  * `bloomberg.py` isolates Desktop/Server session logic and DEMO fallbacks
  * `utils.py` houses calibration, simulation, statistics
* **Frontend**: React + TypeScript + Vite (`/frontend`)

  * Ticker autocomplete → Positions table → Calibration panel → Simulation controls
  * Recharts for paths & distribution

---

## Repository Layout

```
.
├── backend
│   ├── app.py               # FastAPI app & endpoints
│   ├── bloomberg.py         # Desktop/Server API helpers + DEMO
│   ├── models.py            # Pydantic request models
│   ├── utils.py             # math: annualize, corr, simulate, stats
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend
│   ├── Dockerfile
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── .env.example
│   └── src/…                # components, charts, api client
├── docker-compose.yml
├── README.md                # this file
└── postman_collection.json
```

---

## Prerequisites

* **Docker** & **Docker Compose** (Docker Desktop on macOS/Windows, or Docker Engine on Linux)
* **Node 18+ (prefer 20)** for local dev without Docker
* **Python 3.11+** for local backend without Docker
* **Bloomberg**:

  * For containerized runs, **B-PIPE/Server API** is recommended.
  * **Desktop API** generally requires running the backend **on the host**, not in a container (see below).

---

## Quick Start

### Dev (hot reload)

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose --profile dev up --build
```

Open [http://localhost:5173](http://localhost:5173)

### Prod (static frontend + multi-worker backend)

```bash
docker compose --profile prod up --build -d
```

Open [http://localhost:8080](http://localhost:8080)

### Run without Docker (Desktop API users)

If you only have Bloomberg **Desktop API** and you’re on macOS/Windows, run the **backend on the host**:

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export SESSION_MODE=DESKTOP DEMO_MODE=false
uvicorn app:app --host 0.0.0.0 --port 8000

# Frontend
cd ../frontend
npm i
npm run dev -- --host --port 5173
```

> Linux-only best-effort: you may try Docker with `network_mode: host` for the backend, but Desktop API from containers is brittle. On macOS/Windows, Desktop API from containers is effectively a no-go.

---

## Environment Variables

### Back end

`backend/.env`:

| Variable        | Example/Default                               | Purpose                                    |
| --------------- | --------------------------------------------- | ------------------------------------------ |
| `SESSION_MODE`  | `SERVER` \| `DESKTOP`                         | Choose Bloomberg mode (B-PIPE vs Desktop). |
| `BBG_HOST`      | `your_bpipe_host`                             | B-PIPE host/VIP (SERVER mode only).        |
| `BBG_PORT`      | `8194`                                        | B-PIPE port (SERVER mode only).            |
| `DEMO_MODE`     | `true`                                        | Bypass Bloomberg and use synthetic data.   |
| `ALLOW_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | CORS allowlist for the frontend.           |

### Front end

`frontend/.env`:

| Variable            | Example/Default         | Purpose                          |
| ------------------- | ----------------------- | -------------------------------- |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Base URL of the FastAPI backend. |

### Bloomberg Connectivity Scenarios

* **Demo (no Bloomberg)**

  ```
  SESSION_MODE=SERVER
  DEMO_MODE=true
  ```

  (BBG\_\* ignored)

* **Desktop API (Terminal on same machine)**

  * **Recommended:** run backend on host

    ```
    SESSION_MODE=DESKTOP
    DEMO_MODE=false
    ```
  * **Linux-only best-effort:** add `network_mode: host` to backend in compose (dev). Not supported on Docker Desktop (macOS/Windows).

* **B-PIPE / Server API**

  ```
  SESSION_MODE=SERVER
  BBG_HOST=<ask IT or Bloomberg Enterprise>
  BBG_PORT=8194
  DEMO_MODE=false
  ```

  Connectivity test:

  * Linux/macOS: `nc -vz <BBG_HOST> <BBG_PORT>`
  * Windows PowerShell: `Test-NetConnection -ComputerName <BBG_HOST> -Port <BBG_PORT>`

---

## API Reference

Base URL: `http://localhost:8000`

### `POST /api/search`

Request:

```json
{ "query": "appl", "yellowKey": "Equity" }
```

Response:

```json
[
  { "security": "AAPL US Equity", "description": "Apple Inc" },
  ...
]
```

### `POST /api/calibrate`

Request:

```json
{
  "tickers": ["AAPL US Equity","MSFT US Equity"],
  "start": "2023-01-01",
  "end": "2025-08-01",
  "periodicity": "DAILY",
  "adjustSplits": true,
  "adjustDividends": true,
  "useTotalReturnField": false
}
```

Response:

```json
{
  "tickers": ["AAPL US Equity","MSFT US Equity"],
  "paramsPerTicker": { "AAPL US Equity": { "S0": 230.12, "mu": 0.08, "vol": 0.32 }, ... },
  "corr": [[1,0.5],[0.5,1]]
}
```

### `POST /api/simulate`

Request:

```json
{
  "positions":[{"ticker":"AAPL US Equity","qty":100},{"ticker":"MSFT US Equity","qty":-50}],
  "days":20,
  "nSims":2000,
  "driftMode":"flat",
  "useStudentT":true,
  "dof":6,
  "calibration": { "paramsPerTicker": { ... }, "corr": [[1,0.5],[0.5,1]] }
}
```

Response:

```json
{
  "pv0": 123456.78,
  "pnl": [ ... nSims ... ],
  "pathsSample": [ [pv_d1,...,pv_dN], ... up to 500 sims ... ],
  "summary": { "mean": ..., "stdev": ..., "VaR95": ..., "ES95": ..., "probLoss": ... }
}
```

**Notes**

* `corr` **must be N×N** where N = number of tickers in `positions`, aligned to the same order.
* `pathsSample` is capped at 500 sims for UI performance; `pnl` always includes all sims.

---

## Simulation Model

Per asset *i* and day step Δt = 1/252:

$$
\log S_i(t+\Delta t) = \log S_i(t) + \left(\mu_i - \tfrac{1}{2}\sigma_i^2\right)\Delta t + \sigma_i \sqrt{\Delta t}\; \varepsilon_i
$$

* $\varepsilon \sim \mathcal{N}(0, \Sigma)$, with $\Sigma$ the correlation matrix.
* **Student-t heavy tails**: apply **per-simulation** elliptical scaling $Z / \sqrt{\chi^2_\nu/\nu}$.
* **Portfolio PV** per day = $\sum_i \text{qty}_i \cdot S_i(t)$.
* **PnL** = $PV(T) - PV(0)$.
* Stats: mean, stdev, VaR95 (5th pctile), ES95 (tail mean), Prob(loss).

---

## Frontend Usage

1. **Search** for tickers (autocomplete), click to add to **Positions**.
2. Set **quantities** (negative = short).
3. **Calibrate**: choose date range (+ optional Total Return field).
4. **Run Simulation**: pick days, nSims, drift mode (0% vs μ), toggle Student-t + ν.
5. Inspect **Paths** (all lines) and **Distribution**; see **Summary** (PV₀, VaR, ES, etc.).

---

## Troubleshooting

**Vite fails: `Cannot find package '@vitejs/plugin-react'`**
Run in `/frontend`:

```bash
npm install -D @vitejs/plugin-react
npm run dev
```

(Already included in `devDependencies`, but if you copied partial files, reinstall.)

**Simulation error: “could not broadcast … shape (S,S) into (S,1)”**
Cause: `corr` shape mismatch or bad Student-t broadcast (now guarded). Fix:

* Re-run **Calibrate** and then **Simulate** without changing tickers in between.
* Ensure `corr` is **assets×assets (N×N)** and in the **same order** as `positions`.
* With one ticker, `corr` must be `[[1]]`.

**Desktop API from Docker won’t connect**

* On macOS/Windows, run backend on **host**.
* On Linux, try `network_mode: host` (no guarantee).
* Ensure Terminal is running and logged in; entitlement errors surface as API failures.

**CORS errors**

* Set `ALLOW_ORIGINS` in `backend/.env` to match your frontend origin(s).
* Set `VITE_API_BASE_URL` in `frontend/.env` to point at the backend.

**Port conflicts**

* Dev uses 8000 (backend) and 5173 (frontend). Change in compose/Vite if needed.

---

## Acceptance Criteria

* Search returns instruments (or mock list in DEMO).
* Calibration returns μ/σ/corr; S₀ appears in positions table.
* Simulation returns full PnL and up to 500 paths; charts render smoothly.
* `dev` profile: hot reload for both services.
* `prod` profile: static frontend served by Nginx; backend with 2 workers.
* Clear UI errors for connection/entitlement issues; DEMO toggle works.

---

## Limitations & Non-Goals

* No persistence/auth.
* No multi-currency normalization (PnL is raw price × qty).
* No options/IV modeling or greeks.
* Desktop API inside Docker on macOS/Windows is not supported.

---

## Roadmap (nice-to-haves)

* CSV/Parquet export for calibration & simulation results.
* Per-step Student-t volatility shocks (not just per-simulation scaling).
* Currency normalization via FX curves; futures contract multipliers.
* Server-side pagination for /search; retry/backoff on Bloomberg errors.
* Basic auth + saved scenarios.

---

## Postman Collection

`postman_collection.json` includes the three endpoints.
Import into Postman → set environment (base URL `http://localhost:8000`) → run requests in order: **Search → Calibrate → Simulate**.


