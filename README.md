# Electricity Dashboard

**COMP5339 Assignment 2** — NEM electricity generation monitoring dashboard with real-time MQTT data streaming and historical Assignment 1 integration.

## Architecture

```
OpenElectricity API  ──→  CSV Cache  ──→  MQTT Broker  ──→  FastAPI  ──→  SQLite  ──→  React / Streamlit
  (Task 1 notebook)     (Task 2 nb)     (Task 3+6 nb)    (Task 4)     (Task 4)     (Task 5)

Assignment 1 DuckDB  ──→  migrate_a1.py  ──→  SQLite (same)  ──→  FastAPI  ──→  React
  (data/assignment_1.duckdb)                                            ↑
                                                          /api/assignment1/*
```

| Component | Tech | Port |
|---|---|---|
| MQTT Broker | Mosquitto | 1883 |
| Backend API | FastAPI + SQLAlchemy + DuckDB | 8000 |
| React Dashboard | Vite + Leaflet + Recharts + Tailwind | 5173 |

## Data

All data — both MQTT‑streamed NEM measurements and Assignment 1 historical records — is already stored in `data/electricity.db` (93 MB, included in the repo). The dashboard works immediately after `bash start.sh` with no API keys, no notebook execution, and no waiting for streaming data to accumulate.

| Source | Location | Tables | Rows |
|--------|----------|--------|------|
| NEM real-time (MQTT) | `data/electricity.db` | `facilities`, `measurements`, `market_data` | 817,344 measurements + 8,064 market records |
| Assignment 1 history | `data/assignment_1.duckdb` | *(migrated into `data/electricity.db`)* | 32 state‑year rows + 131 projects |

The DuckDB file (`data/assignment_1.duckdb` + `.wal`) is the raw Assignment 1 source. It has been migrated into SQLite via `backend/migrate_a1.py` — no further migration is needed unless the DuckDB is replaced with new data.

## Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Mosquitto** (MQTT broker) — `brew install mosquitto` (macOS) or `apt install mosquitto` (Linux)

### 1. Start

```bash
bash start.sh
```

This single command handles everything: installs Python and React dependencies, starts the MQTT broker, FastAPI backend, and React dashboard. After startup, open:

| Dashboard | URL |
|---|---|
| React | http://localhost:5173 |
| API docs | http://localhost:8000/docs |

> **Prerequisites:** Python 3.10+, Node.js 18+, Mosquitto (`brew install mosquitto` on macOS or `apt install mosquitto` on Linux).

### 2. (Optional) Reproduce the data pipeline

Open `COMP5339_Assignment2.ipynb` and **Run All** to execute Tasks 1–3 and 6 end-to-end: retrieve power/emissions/market data from the OpenElectricity API, integrate and clean, export to CSV, and publish MQTT messages.

## Project Structure

```
electricity-dashboard/
├── start.sh                     # One-command launcher
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── mqtt_mapping.yaml            # MQTT field mapping config
├── data/
│   ├── electricity.db           # SQLite — all live and historical data
│   ├── assignment_1.duckdb      # A1 DuckDB (state-year + projects)
│   └── assignment_1.duckdb.wal
├── backend/
│   ├── main.py                  # FastAPI entry point, lifespan
│   ├── api.py                   # REST endpoints (NEM + A1)
│   ├── database.py              # SQLAlchemy models
│   ├── mqtt_subscriber.py       # MQTT handler — subscribe & store
│   ├── adapter.py               # JSON field mapping adapter
│   ├── migrate_a1.py            # DuckDB → SQLite migration
│   └── config.py                # Settings (.env + YAML)
└── frontend/                    # React + Vite + Leaflet + Recharts
    └── src/
        ├── App.tsx              # Root layout
        ├── components/          # MapView, TopBar, BottomPanel, etc.
        ├── hooks/useApi.ts      # API hooks (NEM + A1)
        └── types/index.ts       # TypeScript interfaces (NEM + A1)
```

## Data Pipeline

1. **Task 1–2 (notebook):** Data is retrieved from the [OpenElectricity API](https://docs.openelectricity.org.au) and integrated into CSV files (`combined_power_emissions.csv`, `market_price_demand.csv`). Unit metadata is exported for the dashboard.
2. **Task 3 (notebook):** Each row of the combined CSV is published to MQTT topic `openelectricity/nem/facility_power_emissions` in chronological order with a 0.1 s delay.
3. **Task 4 (backend):** The MQTT subscriber normalises incoming JSON via `adapter.py`, stores measurements and market data in SQLite, and auto‑registers new facilities. Assignment 1 schema is implemented in `database.py` via `IntegratedEnergyStateYear` and `RenewableProject` tables, populated by `migrate_a1.py`.
4. **Task 5 (frontend):** The React dashboard renders an interactive Leaflet map with carbon‑intensity‑coloured NEM markers, blue A1 renewable project markers, real‑time time‑series charts, market price/demand views, and a Historical (A1) tab with state‑level emissions charts and project summary cards.
5. **Task 6 (notebook):** `run_continuous_publisher()` loops every 60 seconds, re‑loading the CSV and re‑publishing all records to simulate an unbounded data stream (commented out by default).

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/facilities` | All facility metadata |
| `GET` | `/api/facilities/latest` | Latest power + emissions per facility |
| `GET` | `/api/facilities/{id}/timeseries` | Time-series for one facility |
| `GET` | `/api/summary?group_by=region&metric=power_mw` | Aggregated data |
| `GET` | `/api/stats` | System statistics |
| `GET` | `/api/market/latest` | Latest price + demand by region |
| `GET` | `/api/market/timeseries?region=NSW1` | Market time-series |
| `GET` | `/api/assignment1/state_year` | A1 integrated state‑year data |
| `GET` | `/api/assignment1/renewable_projects` | A1 renewable projects (filterable) |
| `GET` | `/api/assignment1/summary` | A1 summary statistics |
