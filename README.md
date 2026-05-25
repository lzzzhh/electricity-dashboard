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
| Streamlit Dashboard | Folium + Plotly | 8501 |

## Data Sources

All data is persisted in `data/electricity.db` (SQLite). No external API calls are made at dashboard runtime.

| Source | Location | Tables | Rows |
|--------|----------|--------|------|
| NEM real-time (MQTT) | *(ingested by mqtt_subscriber.py)* | `facilities`, `measurements`, `market_data`, `raw_mqtt_messages` | 1,601,275 measurements + 8,064 market records |
| Assignment 1 history | `data/assignment_1.duckdb` | `integrated_energy_state_year`, `renewable_projects_geocoded_nominatim_fallback` | 32 state-year rows + 131 projects |

To re-import A1 data from the DuckDB into SQLite, run:

```bash
python -m backend.migrate_a1
```

## Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Mosquitto** (MQTT broker) — `brew install mosquitto` (macOS) or `apt install mosquitto` (Linux)

### 1. Clone & Install

```bash
git clone https://github.com/lzzzhh/electricity-dashboard.git
cd electricity-dashboard

cp .env.example .env
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### 2. (Optional) Reproduce the data pipeline

Open the notebook and **Run All**:

```
COMP5339_Assignment2.ipynb
```

This executes Tasks 1–3 and 6: retrieves power/emissions/market data from the OpenElectricity REST API, integrates and cleans the data, exports it to CSV, and publishes MQTT messages. The last cell (Task 6 continuous loop) is commented out — uncomment it to start looping.

### 3. Start the project

```bash
bash start.sh
```

One command launches the MQTT broker, FastAPI backend, and React frontend. The dashboard uses pre‑loaded data in `electricity.db` — no external API calls are needed.

### 4. Open

| Dashboard | URL |
|---|---|
| **React** (primary) | http://localhost:5173 |
| Streamlit (alternative) | http://localhost:8501 |
| API docs | http://localhost:8000/docs |

## Project Structure

```
electricity-dashboard/
├── COMP5339_Assignment2.ipynb   # Notebook: Tasks 1, 2, 3, 6
├── dashboard.py                 # Streamlit dashboard (Task 5 alt)
├── start.sh                     # One-command launcher
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── mqtt_mapping.yaml            # MQTT field mapping config
├── data/
│   ├── electricity.db           # SQLite — all live and historical data
│   ├── assignment_1.duckdb      # A1 DuckDB (state-year + projects)
│   └── assignment_1.duckdb.wal
├── assignment1/                 # A1 data cleaning and analysis notebooks
│   ├── data_cleaning_integration_augmentation.ipynb
│   └── 3 Analysis+Visualisation.ipynb
├── backend/
│   ├── main.py                  # FastAPI entry point, lifespan
│   ├── api.py                   # REST endpoints (NEM + A1)
│   ├── database.py              # SQLAlchemy models
│   ├── mqtt_subscriber.py       # MQTT handler — subscribe & store
│   ├── adapter.py               # JSON field mapping adapter
│   ├── migrate_a1.py            # DuckDB → SQLite migration
│   └── config.py                # Settings (.env + YAML)
├── frontend/                    # React + Vite + Leaflet + Recharts
│   └── src/
│       ├── App.tsx              # Root layout
│       ├── components/          # MapView, TopBar, BottomPanel, etc.
│       ├── hooks/useApi.ts      # API hooks (NEM + A1)
│       └── types/index.ts       # TypeScript interfaces (NEM + A1)
└── report/
    ├── template.tex
    └── template.tex.zip
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
