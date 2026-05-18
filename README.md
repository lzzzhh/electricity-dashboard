# Electricity Dashboard

**COMP5339 Assignment 2** — NEM electricity generation monitoring dashboard with real-time MQTT data streaming.

## Architecture

```
OpenElectricity API → CSV Cache → MQTT Broker → FastAPI → SQLite → React / Streamlit
     (Task 1)         (Task 2)    (Task 3+6)   (Task 4)   (Task 4)    (Task 5)
```

| Component | Tech | Port |
|---|---|---|
| MQTT Broker | Mosquitto | 1883 |
| Backend API | FastAPI + SQLAlchemy | 8000 |
| React Dashboard | Vite + Leaflet + Recharts | 5173 |
| Streamlit Dashboard | Folium + Plotly | 8501 |
| Publisher | Python (replays CSV to MQTT) | — |

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

### 2. Start

```bash
bash start.sh
```

That's it. The script launches the MQTT broker, FastAPI backend, React frontend, and CSV-to-MQTT publisher in one command.

### 3. Open

| Dashboard | URL |
|---|---|
| **React** (primary) | http://localhost:5173 |
| Streamlit (alternative) | http://localhost:8501 |
| API docs | http://localhost:8000/docs |

## Project Structure

```
electricity-dashboard/
├── backend/                  # FastAPI + SQLAlchemy
│   ├── main.py               # App entry point, lifespan
│   ├── api.py                # REST endpoints
│   ├── database.py           # SQLAlchemy models (Facility, Measurement, MarketData)
│   ├── mqtt_subscriber.py    # MQTT message handler + storage
│   ├── adapter.py            # JSON field mapping adapter
│   └── config.py             # Settings loader (.env + YAML)
├── frontend/                 # React + Vite + Tailwind
│   └── src/
│       ├── App.tsx           # Root layout
│       ├── components/       # MapView, TopBar, BottomPanel, etc.
│       ├── hooks/useApi.ts   # API data fetching hooks
│       └── types/index.ts    # TypeScript interfaces
├── dashboard.py              # Streamlit dashboard (Python)
├── run_publisher.py          # CSV → MQTT replay (continuous mode)
├── mqtt_mapping.yaml         # Field mapping config
├── start.sh                  # One-command launcher
├── requirements.txt          # Python dependencies
└── .env.example              # Environment template
```

## Data Pipeline

1. **Task 1–2:** Data is retrieved from the [OpenElectricity API](https://docs.openelectricity.org.au) and cached as CSV files (`combined_power_emissions.csv`, `market_price_demand.csv`).
2. **Task 3:** `run_publisher.py` replays the CSV records to MQTT topic `openelectricity/nem/facility_power_emissions` in chronological order with a 0.1 s delay.
3. **Task 4:** The backend MQTT subscriber normalises incoming JSON via `adapter.py`, stores measurements and market data in SQLite, and auto-registers new facilities.
4. **Task 5:** The React dashboard renders an interactive Leaflet map with carbon-intensity-coloured markers, filterable by region and fuel technology, with time-series charts and market price/demand views.
5. **Task 6:** The publisher loops continuously with a 60 s delay between rounds, simulating an unbounded stream.

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
