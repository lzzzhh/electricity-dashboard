"""Electricity Dashboard — v7.0
Operational map-first dashboard. Electricity Maps inspired, assignment-compliant.
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ═══════════════════════
# Config — colours & labels
# ═══════════════════════
API_BASE = "http://localhost:8000"

# Fuel-tech palette for source breakdown / reference; markers use CI scale
FUEL_COLORS = {
    "coal_black": "#5c3a24", "coal_brown": "#7d5240",
    "gas_ccgt":   "#e65100", "gas_ocgt":   "#ff8f00",
    "hydro":      "#29b6f6", "battery":    "#66bb6a",
    "wind":       "#81c784", "solar":      "#ffd600",
    "bioenergy":  "#8d6e63", "load":       "#78909c",
}

# Carbon-intensity colour scale — used for marker colour
CARBON_SCALE = [
    (50,   "#2ecc71"),   # very low
    (150,  "#8bc34a"),   # low
    (300,  "#fdd835"),   # medium
    (500,  "#ff9800"),   # high
    (800,  "#f4511e"),   # very high
    (1200, "#c62828"),   # extreme
]

CI_LABELS = [
    (50,   "very low"),
    (150,  "low"),
    (300,  "medium"),
    (500,  "high"),
    (800,  "very high"),
    (1200, "extreme"),
]

FUEL_LABELS = {
    "coal_black": "Coal (black)", "coal_brown": "Coal (brown)",
    "gas_ccgt": "Gas (CCGT)", "gas_ocgt": "Gas (OCGT)",
    "hydro": "Hydro", "battery": "Battery storage",
    "wind": "Wind", "solar": "Solar", "bioenergy": "Biomass",
    "load": "Dispatchable Load",
}

# Region colors for market charts
REGION_COLORS = {
    "NSW1": "#e65100", "QLD1": "#8e24aa",
    "VIC1": "#1565c0", "SA1":  "#fdd835",
    "TAS1": "#2e7d32",
}


def carbon_color(val):
    """Map gCO₂eq/kWh to hex colour."""
    if val <= 0:
        return "#2ecc71"
    for t, c in CARBON_SCALE:
        if val < t:
            return c
    return CARBON_SCALE[-1][1]


def ci_label(val):
    """Human-readable carbon-intensity band."""
    for t, lbl in CI_LABELS:
        if val < t:
            return lbl
    return CI_LABELS[-1][1]


# ═══════════════════════
# Page config
# ═══════════════════════
st.set_page_config(
    page_title="NEM Electricity Monitor",
    page_icon="⚡",
    layout="wide",
)

# ═══════════════════════
# CSS — restrained professional theme
# ═══════════════════════
st.markdown("""
<style>
    :root {
        --bg:       #f7f8fa;
        --surface:  #ffffff;
        --border:   #e4e4ea;
        --text:     #1a1a24;
        --text-2:   #5a5a6e;
        --text-3:   #90909e;
        --accent:   #e65100;
        --online:   #2e7d32;
        --hover:    #f0f0f4;
    }
    .stApp { background: var(--bg); }
    .main .block-container { padding: 0 !important; max-width: 100% !important; }

    /* Typography */
    h1 { font-weight: 600 !important; font-size: 1rem !important; color: var(--text) !important; margin: 0 !important; }
    h2 { font-size: 0.6rem !important; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-3) !important; margin: 0 !important; }
    p, span, div { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; color: var(--text-2); }
    hr { border-color: var(--border) !important; margin: 4px 0 !important; }
    .stCaption { color: var(--text-3) !important; font-size: 0.62rem; }

    /* ===== SIDEBAR — narrow control panel ===== */
    [data-testid="stSidebar"] {
        background: var(--surface) !important;
        border-right: 1px solid var(--border) !important;
        min-width: 250px !important; max-width: 250px !important;
    }
    [data-testid="stSidebar"] .block-container { padding: 0.5rem 0.5rem !important; }

    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label {
        color: var(--text-3) !important; font-size: 0.6rem !important;
        text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-bottom: 2px !important;
    }
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div,
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] > div {
        background: var(--bg) !important; border: 1px solid var(--border) !important;
        border-radius: 4px !important; font-size: 0.76rem !important;
    }
    [data-testid="stSidebar"] span[data-baseweb="tag"] {
        background: #e8e8ed !important; color: var(--text-2) !important; border-radius: 3px !important; font-size: 0.68rem !important;
    }

    /* Zone list buttons */
    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important; color: var(--text-2) !important;
        border: none !important; text-align: left !important;
        padding: 3px 6px !important; font-size: 0.74rem !important; font-weight: 400 !important;
        border-radius: 4px !important; width: 100% !important;
        transition: background 0.1s !important; min-height: 24px !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: var(--hover) !important; color: var(--text) !important;
    }

    /* ===== TOP STATUS BAR ===== */
    .top-bar {
        display: flex; align-items: center; gap: 14px;
        padding: 6px 14px; background: var(--surface);
        border-bottom: 1px solid var(--border);
        flex-wrap: wrap;
    }
    .top-bar .app-title { color: var(--text); font-weight: 600; font-size: 0.9rem; }
    .top-bar .chip {
        font-size: 0.64rem; color: var(--text-2);
        background: var(--bg); padding: 2px 8px; border-radius: 10px;
        display: inline-flex; align-items: center; gap: 4px;
    }
    .top-bar .chip .dot { width: 5px; height: 5px; border-radius: 50%; display: inline-block; }

    /* ===== MAP ===== */
    .map-wrapper {
        padding: 0; margin: 0;
    }

    /* ===== RIGHT DETAIL PANEL ===== */
    .detail-card {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 6px; padding: 12px 14px; margin: 6px 6px 6px 0;
        overflow-y: auto; max-height: calc(100vh - 180px);
    }
    .detail-card .fac-name { font-size: 1rem; color: var(--text); font-weight: 600; margin-bottom: 1px; }
    .detail-card .fac-meta { font-size: 0.65rem; color: var(--text-3); margin-bottom: 8px; }
    .detail-card .ci-big { font-size: 2rem; font-weight: 300; line-height: 1; }
    .detail-card .ci-unit { font-size: 0.72rem; color: var(--text-3); }
    .detail-card .ci-label { font-size: 0.58rem; color: var(--text-3); text-transform: uppercase; letter-spacing: 1px; margin-top: 1px; }

    .kpi-row { display: flex; gap: 6px; margin: 8px 0; }
    .kpi-row .kpi {
        flex: 1; text-align: center; background: var(--bg);
        border-radius: 4px; padding: 6px 4px;
    }
    .kpi-row .kpi .val { font-size: 0.9rem; font-weight: 600; }
    .kpi-row .kpi .unit { font-size: 0.55rem; color: var(--text-3); text-transform: uppercase; }

    .src-row {
        display: flex; align-items: center; gap: 5px; padding: 1px 0; font-size: 0.66rem;
    }
    .src-row .src-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
    .src-row .src-name { color: var(--text-2); flex: 0 0 72px; font-size: 0.62rem; }
    .src-row .src-bar { flex: 1; height: 4px; background: #e8e8ed; border-radius: 2px; overflow: hidden; }
    .src-row .src-bar-fill { height: 100%; border-radius: 2px; }
    .src-row .src-pct { color: var(--text-3); font-size: 0.6rem; min-width: 28px; text-align: right; }
    .src-row .src-val { color: #b0b0be; font-size: 0.58rem; min-width: 44px; text-align: right; }

    .section-hdr {
        font-size: 0.56rem; color: var(--text-3); text-transform: uppercase;
        letter-spacing: 1px; margin: 10px 0 2px 0;
    }

    .empty-state {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 6px; padding: 40px 16px; text-align: center; margin: 6px 6px 6px 0;
    }
    .empty-state .msg { font-size: 0.75rem; color: var(--text-3); }
    .empty-state .sub  { font-size: 0.62rem; color: #bbb; margin-top: 2px; }

    /* ===== BOTTOM BAR ===== */
    .bottom-bar {
        display: flex; align-items: center; gap: 10px;
        padding: 4px 14px; font-size: 0.66rem; color: var(--text-3);
        border-top: 1px solid var(--border); background: var(--surface);
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0; background: transparent; border-bottom: 1px solid var(--border);
        padding: 0 14px;
    }
    .stTabs [data-baseweb="tab"] {
        color: var(--text-3); font-size: 0.68rem; border-radius: 0; padding: 5px 12px;
    }
    .stTabs [aria-selected="true"] {
        color: var(--text); border-bottom: 2px solid var(--accent);
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 3px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #ddd; border-radius: 2px; }

    /* DataFrame */
    .stDataFrame { font-size: 0.68rem; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════
# Data loading
# ═══════════════════════
@st.cache_data(ttl=30)
def _get(url, timeout=5):
    try:
        return requests.get(f"{API_BASE}{url}", timeout=timeout).json()
    except Exception:
        return [] if url != "/api/stats" else {}


facilities = _get("/api/facilities")
latest = _get("/api/facilities/latest")
stats = _get("/api/stats")
market_latest = _get("/api/market/latest")
market_regions = _get("/api/market/regions")

# Assignment 1 historical data
a1_summary = _get("/api/assignment1/summary")
a1_state_year = _get("/api/assignment1/state_year")
a1_renewable = _get("/api/assignment1/renewable_projects?geocoded_only=true")

fac_lookup = {f["facility_id"]: f for f in facilities}
latest_lookup = {d["facility_id"]: d for d in latest}
all_regions = sorted(set(f.get("network_region", "") for f in facilities))
all_fuels = sorted(set(f.get("fuel_tech", "") for f in facilities))

if "sel" not in st.session_state:
    st.session_state.sel = None
if "metric" not in st.session_state:
    st.session_state.metric = "power_mw"
if "market_region" not in st.session_state:
    st.session_state.market_region = "NSW1"

st_autorefresh(interval=4000, key="refresh")

# ═══════════════════════
# SIDEBAR —  control panel
# ═══════════════════════
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:6px;padding:0 0 4px 0;">
        <span style="font-size:0.95rem;color:var(--accent);">⚡</span>
        <span style="font-size:0.85rem;color:var(--text);font-weight:600;">NEM Monitor</span>
    </div>
    """, unsafe_allow_html=True)

    st.session_state.metric = st.selectbox(
        "Metric",
        ["power_mw", "emissions_tco2e"],
        format_func=lambda x: "Power (MW)" if x == "power_mw" else "Carbon intensity",
    )

    regions = st.multiselect("Regions", all_regions, default=all_regions, placeholder="All regions")
    fuels = st.multiselect("Technology", all_fuels, default=all_fuels, placeholder="All technologies")

    # Data stats
    st.markdown(f"""
    <div style="display:flex;gap:10px;padding:2px 4px;margin:2px 0;font-size:0.62rem;color:var(--text-3);">
        <span><b style="color:var(--text);">{stats.get('facilities_total',0)}</b> units</span>
        <span><b style="color:var(--text);">{stats.get('measurements_total',0):,}</b> records</span>
    </div>
    """, unsafe_allow_html=True)

    if stats.get("last_measurement_ts"):
        st.caption(f"Data through {stats['last_measurement_ts'][:19].replace('T',' ')}")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h2>Facilities</h2>", unsafe_allow_html=True)

    filtered = [f for f in facilities if f.get("network_region") in regions and f.get("fuel_tech") in fuels]

    for f in filtered:
        fid = f["facility_id"]
        d = latest_lookup.get(fid, {})
        pwr = d.get("power_mw", 0)
        em = d.get("emissions_tco2e", 0)
        name = f.get("facility_name", fid)
        ci = (em * 1000) / max(pwr, 1)
        dot = carbon_color(ci)

        c1, c2 = st.columns([0.12, 0.88])
        with c1:
            st.markdown(f"""<div style="display:flex;align-items:center;justify-content:center;height:24px;">
                <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:{dot};"></span>
            </div>""", unsafe_allow_html=True)
        with c2:
            if st.button(f"{name}  —  {pwr:.0f} MW", key=f"z_{fid}", use_container_width=True):
                st.session_state.sel = fid

# ═══════════════════════
# TOP STATUS BAR
# ═══════════════════════
facility_cnt = stats.get("facilities_total", 0)
msg_cnt = stats.get("measurements_total", 0)
market_cnt = stats.get("market_records", 0)
last_ts = (stats.get("last_measurement_ts") or "")[:19].replace("T", " ")
metric_label = "Power (MW)" if st.session_state.metric == "power_mw" else "Carbon intensity"

st.markdown(f"""
<div class="top-bar">
    <span class="app-title">NEM Electricity Monitor</span>
    <span class="chip"><span class="dot" style="background:var(--online);"></span> CSV data loaded</span>
    <span class="chip">NEM &middot; Australia</span>
    <span class="chip">Metric: {metric_label}</span>
    <span style="margin-left:auto;font-size:0.62rem;color:var(--text-3);">
        {facility_cnt} units &middot; {msg_cnt:,} records &middot; {market_cnt:,} market pts &middot; {last_ts}
    </span>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════
# MAIN — Map + Detail
# ═══════════════════════
col_map, col_right = st.columns([3.5, 1.5])

# ═══════════════════════
# MAP
# ═══════════════════════
with col_map:
    m = folium.Map(
        location=[-33, 145],
        zoom_start=5,
        tiles="CartoDB positron",
        control_scale=False,
        zoom_control=True,
    )

    for d in latest:
        fid = d.get("facility_id")
        meta = fac_lookup.get(fid, {})
        if meta.get("network_region") not in regions:
            continue
        if meta.get("fuel_tech") not in fuels:
            continue

        lat = meta.get("latitude", 0)
        lon = meta.get("longitude", 0)
        name = meta.get("facility_name", fid)
        region = meta.get("network_region", "")
        fuel = meta.get("fuel_tech", "")
        fuel_label = FUEL_LABELS.get(fuel, fuel)
        pwr = d.get("power_mw", 0)
        em = d.get("emissions_tco2e", 0)
        ts = d.get("timestamp", "")[:19]
        ci = (em * 1000) / max(pwr, 1)
        ci_c = carbon_color(ci)
        ci_band = ci_label(ci)

        # Marker size proportional to power
        radius = max(5, min(16, pwr / 180))

        # Popup — all required fields
        popup = f"""
        <div style="font-family:-apple-system,sans-serif;background:#fff;color:var(--text-2);min-width:170px;border-radius:4px;">
            <div style="font-size:0.82rem;color:#1a1a24;font-weight:600;margin-bottom:1px;">{name}</div>
            <div style="font-size:0.6rem;color:#90909e;margin-bottom:5px;">{fuel_label} &middot; NEM {region}</div>
            <div style="display:flex;gap:5px;margin-bottom:3px;">
                <div style="flex:1;text-align:center;background:#f5f5f8;border-radius:3px;padding:4px 6px;">
                    <div style="font-size:0.82rem;font-weight:600;color:{ci_c};">{ci:.0f}</div>
                    <div style="font-size:0.5rem;color:#90909e;">gCO₂/kWh</div>
                </div>
                <div style="flex:1;text-align:center;background:#f5f5f8;border-radius:3px;padding:4px 6px;">
                    <div style="font-size:0.82rem;font-weight:600;color:#e65100;">{pwr:.0f}</div>
                    <div style="font-size:0.5rem;color:#90909e;">MW</div>
                </div>
            </div>
            <div style="font-size:0.52rem;color:#bbb;">{ci_band} carbon &middot; {ts}</div>
        </div>"""

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=ci_c,
            weight=1.5,
            fill=True,
            fill_color=ci_c,
            fill_opacity=0.82,
            popup=folium.Popup(popup, max_width=220),
            tooltip=f"<b>{name}</b><br>{pwr:.0f} MW &middot; {ci:.0f} gCO₂/kWh",
        ).add_to(m)

    # Carbon-intensity legend — positioned bottom-right of map
    legend = """
    <div style="position:fixed;bottom:36px;left:268px;z-index:9999;
        background:rgba(255,255,255,0.95);border:1px solid #ddd;border-radius:6px;
        padding:6px 8px;font-family:-apple-system,sans-serif;">
        <div style="font-size:0.5rem;color:#90909e;text-transform:uppercase;letter-spacing:1px;">Carbon intensity</div>
        <div style="font-size:0.44rem;color:#bbb;margin-bottom:3px;">gCO₂eq/kWh</div>
        <div style="display:flex;align-items:stretch;gap:2px;">
            <div style="width:6px;height:60px;border-radius:2px;
                background:linear-gradient(to bottom,#2ecc71,#8bc34a,#fdd835,#ff9800,#f4511e,#c62828);"></div>
            <div style="display:flex;flex-direction:column;justify-content:space-between;height:60px;font-size:0.4rem;color:#bbb;padding-left:1px;">
                <span>0</span><span>150</span><span>300</span><span>500</span><span>800</span><span>1200</span>
            </div>
        </div>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))

    st_folium(m, height=650, returned_objects=[])

# ═══════════════════════
# RIGHT PANEL — facility detail (native Streamlit components)
# ═══════════════════════
with col_right:
    sid = st.session_state.sel

    if sid is None or sid not in fac_lookup or sid not in latest_lookup:
        st.info("**Select a facility**\n\nClick a marker on the map or choose from the zone list.")
    else:
        sel_meta = fac_lookup[sid]
        sel_data = latest_lookup[sid]

        name = sel_meta["facility_name"]
        region = sel_meta.get("network_region", "")
        fuel = sel_meta.get("fuel_tech", "")
        fuel_label = FUEL_LABELS.get(fuel, fuel)
        pwr_val = sel_data.get("power_mw", 0) or 0
        emiss_val = sel_data.get("emissions_tco2e", 0) or 0
        ts = (sel_data.get("timestamp", "") or "")[:19]
        ci = (emiss_val * 1000) / max(abs(pwr_val) if pwr_val != 0 else 1, 1)
        ci_c = carbon_color(ci)

        # Facility title
        st.subheader(f"{fuel_label} · NEM {region}")
        st.caption(name)

        # KPI metrics
        c_kpi1, c_kpi2, c_kpi3 = st.columns(3)
        c_kpi1.metric("Power", f"{pwr_val:,.0f} MW")
        c_kpi2.metric("Emissions", f"{emiss_val:,.1f} tCO₂e")
        c_kpi3.metric("Carbon Intensity", f"{ci:.0f} gCO₂/kWh", 
                       delta=ci_label(ci), delta_color="off")
        if ts:
            st.caption(f"Timestamp: {ts}")

        # Source mix
        try:
            sm = _get(f"/api/summary?group_by=fuel_tech&metric={st.session_state.metric}")
            if sm:
                df = pd.DataFrame(sm, columns=["fuel", "value"])
                df = df[df["value"] > 0]
                if not df.empty:
                    df["label"] = df["fuel"].map(FUEL_LABELS)
                    df["pct"] = df["value"] / df["value"].sum() * 100
                    df = df.sort_values("value", ascending=False)
                    with st.expander("Electricity mix (NEM-wide)", expanded=True):
                        for _, row in df.iterrows():
                            st.caption(f"{row['label']}: {row['value']:,.0f} MW ({row['pct']:.1f}%)")
        except Exception:
            pass

        # Timeseries charts
        try:
            ts_data = _get(f"/api/facilities/{sid}/timeseries", timeout=5)
            if ts_data:
                df_ts = pd.DataFrame(ts_data)
                if not df_ts.empty and "timestamp" in df_ts.columns:
                    df_ts["timestamp"] = pd.to_datetime(df_ts["timestamp"])
                    df_ts = df_ts.sort_values("timestamp")
                    df_ts["ci"] = df_ts["emissions_tco2e"] * 1000 / df_ts["power_mw"].clip(lower=1)

                    fig_ci = go.Figure()
                    fig_ci.add_trace(go.Scatter(
                        x=df_ts["timestamp"], y=df_ts["ci"],
                        mode="lines", line=dict(color=ci_c, width=1.5),
                        fill="tozeroy", fillcolor="rgba(180,180,190,0.12)",
                    ))
                    fig_ci.update_layout(
                        title="Carbon intensity (gCO₂/kWh)",
                        margin=dict(l=10, r=10, t=30, b=10), height=150,
                        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                        font=dict(color="#90909e", size=8),
                        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#eee"),
                    )
                    st.plotly_chart(fig_ci, use_container_width=True, config={"displayModeBar": False})

                    fig_pwr = go.Figure()
                    fig_pwr.add_trace(go.Scatter(
                        x=df_ts["timestamp"], y=df_ts["power_mw"],
                        mode="lines", line=dict(color="#e65100", width=1.5),
                        fill="tozeroy", fillcolor="rgba(230,81,0,0.08)",
                    ))
                    fig_pwr.update_layout(
                        title="Power output (MW)",
                        margin=dict(l=10, r=10, t=30, b=10), height=150,
                        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                        font=dict(color="#90909e", size=8),
                        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#eee"),
                    )
                    st.plotly_chart(fig_pwr, use_container_width=True, config={"displayModeBar": False})
        except Exception:
            pass

# ═══════════════════════
# BOTTOM — charts & table
# ═══════════════════════
now_str = datetime.now().strftime("%b %-d, %Y %H:%M")
st.markdown(f"""
<div class="bottom-bar">
    <span>{now_str} &middot; Historical</span>
    <span style="color:#ddd;">|</span>
    <span>Auto-refresh 4s</span>
    <span style="color:#ddd;">|</span>
    <span>{facility_cnt} dispatch units &middot; {msg_cnt:,} measurements</span>
    <span style="margin-left:auto;">Data: NEM 5-min dispatch &middot; May 1-7, 2026</span>
</div>
""", unsafe_allow_html=True)

t1, t2, t3, t4, t5, t6 = st.tabs(["By Region", "By Technology", "Market Prices", "Demand", "Latest Data", "Historical (A1)"])

metric_is_power = st.session_state.metric == "power_mw"

with t1:
    try:
        from plotly.express import bar
        sr = _get(f"/api/summary?group_by=region&metric={st.session_state.metric}")
        if sr:
            df = pd.DataFrame(sr, columns=["region", "value"])
            df = df[df["region"].notna() & (df["region"] != "")]
            title = "Avg Power by Region (MW)" if metric_is_power else "Avg Emissions by Region (tCO₂e)"
            fig = bar(
                df, x="region", y="value", title=title, color="region",
                color_discrete_sequence=["#e65100", "#ff8f00", "#4fc3f7", "#81c784", "#fdd835"],
            )
            fig.update_layout(
                paper_bgcolor="#f7f8fa", plot_bgcolor="#f7f8fa",
                font=dict(color="#5a5a6e", size=10), showlegend=False,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#e4e4ea"),
                title_font=dict(color="#1a1a24", size=11),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except Exception:
        st.caption("Region data unavailable")

with t2:
    try:
        sf = _get(f"/api/summary?group_by=fuel_tech&metric={st.session_state.metric}")
        if sf:
            df = pd.DataFrame(sf, columns=["fuel", "value"])
            df = df[df["fuel"].notna() & (df["fuel"] != "")]
            df["label"] = df["fuel"].map(FUEL_LABELS)
            title = "Avg Power by Technology (MW)" if metric_is_power else "Avg Emissions by Technology (tCO₂e)"
            fig = bar(
                df, x="label", y="value", title=title, color="fuel",
                color_discrete_map=FUEL_COLORS,
            )
            fig.update_layout(
                paper_bgcolor="#f7f8fa", plot_bgcolor="#f7f8fa",
                font=dict(color="#5a5a6e", size=10), showlegend=False,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#e4e4ea"),
                title_font=dict(color="#1a1a24", size=11),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except Exception:
        st.caption("Technology data unavailable")

# ── Market Prices Tab ──
with t3:
    col_price_left, col_price_right = st.columns([2, 1])

    with col_price_left:
        try:
            # 所有区域电价时间序列
            mr = _get("/api/market/timeseries", timeout=10)
            if mr:
                df_p = pd.DataFrame(mr)
                df_p["timestamp"] = pd.to_datetime(df_p["timestamp"])
                fig = go.Figure()
                for region in sorted(df_p["region"].unique()):
                    rdf = df_p[df_p["region"] == region]
                    color = REGION_COLORS.get(region, "#888")
                    fig.add_trace(go.Scatter(
                        x=rdf["timestamp"], y=rdf["price_aud_mwh"],
                        mode="lines", name=region, line=dict(color=color, width=1.2),
                    ))
                fig.update_layout(
                    title="NEM Regional Price (AUD/MWh)",
                    paper_bgcolor="#f7f8fa", plot_bgcolor="#f7f8fa",
                    font=dict(color="#5a5a6e", size=10),
                    margin=dict(l=10, r=10, t=30, b=10),
                    legend=dict(orientation="h", y=1.12, font=dict(size=9)),
                    xaxis=dict(showgrid=False, title=None),
                    yaxis=dict(showgrid=True, gridcolor="#e4e4ea", title="AUD/MWh"),
                    title_font=dict(color="#1a1a24", size=11),
                    height=320,
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        except Exception:
            st.caption("Price data unavailable")

    with col_price_right:
        try:
            if market_latest:
                df_mp = pd.DataFrame(market_latest)
                df_mp = df_mp.sort_values("price_aud_mwh", ascending=False)
                st.markdown("""<div style="font-size:0.65rem;color:#90909e;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">Latest Price</div>""", unsafe_allow_html=True)
                for _, r in df_mp.iterrows():
                    region = r["region"]
                    price = r["price_aud_mwh"]
                    c = REGION_COLORS.get(region, "#888")
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:6px;padding:3px 0;font-size:0.72rem;">
                        <span style="width:8px;height:8px;border-radius:50%;background:{c};flex-shrink:0;"></span>
                        <span style="color:#1a1a24;font-weight:500;min-width:32px;">{region}</span>
                        <span style="color:#5a5a6e;margin-left:auto;">${price:,.2f}</span>
                    </div>
                    """, unsafe_allow_html=True)

                # 区域选择器用于需求明细
                st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)
                st.session_state.market_region = st.selectbox(
                    "Focus region",
                    sorted(df_p["region"].unique()) if mr else ["NSW1", "QLD1", "VIC1", "SA1", "TAS1"],
                    key="market_region_select",
                )
        except Exception:
            pass

# ── Demand Tab ──
with t4:
    try:
        mr_all = _get("/api/market/timeseries", timeout=10)
        if mr_all:
            df_d = pd.DataFrame(mr_all)
            df_d["timestamp"] = pd.to_datetime(df_d["timestamp"])

            # 按区域筛选
            sel_region = st.session_state.get("market_region", "NSW1")
            rdf = df_d[df_d["region"] == sel_region]

            col_d1, col_d2 = st.columns([2, 1])

            with col_d1:
                if not rdf.empty:
                    # 需求时间序列
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=rdf["timestamp"], y=rdf["demand_mw"],
                        mode="lines", fill="tozeroy", fillcolor="rgba(230,81,0,0.08)",
                        line=dict(color="#e65100", width=1.5),
                        name=f"{sel_region} Demand",
                    ))
                    fig.update_layout(
                        title=f"{sel_region} Demand (MW)",
                        paper_bgcolor="#f7f8fa", plot_bgcolor="#f7f8fa",
                        font=dict(color="#5a5a6e", size=10),
                        margin=dict(l=10, r=10, t=30, b=10),
                        xaxis=dict(showgrid=False, title=None),
                        yaxis=dict(showgrid=True, gridcolor="#e4e4ea", title="MW"),
                        title_font=dict(color="#1a1a24", size=11),
                        height=280,
                    )
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            with col_d2:
                # 区域需求对比
                regions_demand = df_d.groupby("region")["demand_mw"].mean().sort_values(ascending=False)
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=regions_demand.index.tolist(),
                    y=regions_demand.values.tolist(),
                    marker_color=[REGION_COLORS.get(r, "#888") for r in regions_demand.index],
                ))
                fig2.update_layout(
                    title="Avg Demand by Region",
                    paper_bgcolor="#f7f8fa", plot_bgcolor="#f7f8fa",
                    font=dict(color="#5a5a6e", size=10), showlegend=False,
                    margin=dict(l=10, r=10, t=30, b=10),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor="#e4e4ea", title="MW"),
                    title_font=dict(color="#1a1a24", size=11),
                    height=280,
                )
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

            # Price vs Demand scatter
            st.markdown("""<div style="font-size:0.65rem;color:#90909e;text-transform:uppercase;letter-spacing:1px;margin-top:8px;">Price vs Demand</div>""", unsafe_allow_html=True)
            fig3 = go.Figure()
            for region in sorted(df_d["region"].unique()):
                rdf_pd = df_d[df_d["region"] == region]
                c = REGION_COLORS.get(region, "#888")
                fig3.add_trace(go.Scatter(
                    x=rdf_pd["demand_mw"], y=rdf_pd["price_aud_mwh"],
                    mode="markers", name=region, marker=dict(color=c, size=3, opacity=0.5),
                ))
            fig3.update_layout(
                paper_bgcolor="#f7f8fa", plot_bgcolor="#f7f8fa",
                font=dict(color="#5a5a6e", size=10),
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", y=1.12, font=dict(size=9)),
                xaxis=dict(showgrid=True, gridcolor="#e4e4ea", title="Demand (MW)"),
                yaxis=dict(showgrid=True, gridcolor="#e4e4ea", title="Price (AUD/MWh)"),
                height=280,
            )
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    except Exception:
        st.caption("Demand data unavailable")

with t5:
    if latest:
        rows = []
        for d in latest[:20]:
            meta = fac_lookup.get(d["facility_id"], {})
            ci_raw = d.get("emissions_tco2e", 0) * 1000 / max(d.get("power_mw", 1), 1)
            rows.append({
                "Facility": meta.get("facility_name", d["facility_id"]),
                "Region": meta.get("network_region", ""),
                "Technology": FUEL_LABELS.get(meta.get("fuel_tech", ""), meta.get("fuel_tech", "")),
                "Power (MW)": f"{d.get('power_mw', 0):,.0f}",
                "Emissions (tCO₂e)": f"{d.get('emissions_tco2e', 0):,.1f}",
                "CI (gCO₂/kWh)": f"{ci_raw:.0f}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── Historical Tab (Assignment 1) ──
with t6:
    if not a1_summary or not a1_state_year:
        st.caption("Assignment 1 data not available. Run `python -m backend.migrate_a1` first.")
    else:
        # ── Summary Stats ──
        st.markdown("""<div style="font-size:0.65rem;color:#90909e;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Assignment 1 — Historical Energy & Economy Data</div>""", unsafe_allow_html=True)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("State-Year Rows", a1_summary.get("state_year_rows", 0))
        c2.metric("Years", "–".join(str(y) for y in a1_summary.get("years", [])))
        c3.metric("Renewable Projects", a1_summary.get("total_renewable_projects", 0))
        c4.metric("Geocoded Projects", a1_summary.get("geocoded_renewable_projects", 0))
        c5.metric("Match Rate", f"{a1_summary.get('match_rate', 0):.1%}")

        # ── Emissions by State ──
        st.markdown("""<div style="font-size:0.65rem;color:#90909e;text-transform:uppercase;letter-spacing:1px;margin-top:10px;">Total Emissions by State</div>""", unsafe_allow_html=True)
        if a1_state_year:
            df_sy = pd.DataFrame(a1_state_year)
            df_em = df_sy.groupby("state")["total_emissions_tco2e"].sum().sort_values(ascending=False)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_em.index.tolist(),
                y=df_em.values.tolist(),
                marker_color=["#c62828", "#e65100", "#fdd835", "#2e7d32", "#1565c0", "#8e24aa", "#ff8f00", "#78909c"][:len(df_em)],
            ))
            fig.update_layout(
                title="Total Emissions by State 2020-2023 (tCO₂e)",
                paper_bgcolor="#f7f8fa", plot_bgcolor="#f7f8fa",
                font=dict(color="#5a5a6e", size=10), showlegend=False,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#e4e4ea"),
                title_font=dict(color="#1a1a24", size=11),
                height=280,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # ── Renewable Capacity + Emissions (two columns) ──
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("""<div style="font-size:0.65rem;color:#90909e;text-transform:uppercase;letter-spacing:1px;">Renewable Capacity vs Emissions</div>""", unsafe_allow_html=True)
            if a1_state_year:
                df_sy = pd.DataFrame(a1_state_year)
                df_plot = df_sy.dropna(subset=["total_renewable_capacity_mw", "total_emissions_tco2e"])
                if not df_plot.empty:
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(
                        x=df_plot["total_renewable_capacity_mw"],
                        y=df_plot["total_emissions_tco2e"],
                        mode="markers+text",
                        text=df_plot["state"] + " " + df_plot["year"].astype(str),
                        textposition="top center",
                        textfont=dict(size=8, color="#5a5a6e"),
                        marker=dict(size=8, color="#e65100", opacity=0.7),
                    ))
                    fig2.update_layout(
                        paper_bgcolor="#f7f8fa", plot_bgcolor="#f7f8fa",
                        font=dict(color="#5a5a6e", size=10), showlegend=False,
                        margin=dict(l=10, r=10, t=10, b=10),
                        xaxis=dict(showgrid=True, gridcolor="#e4e4ea", title="Renewable Capacity (MW)"),
                        yaxis=dict(showgrid=True, gridcolor="#e4e4ea", title="Emissions (tCO₂e)"),
                        height=280,
                    )
                    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.caption("No renewable capacity data available")

        with col_b:
            st.markdown("""<div style="font-size:0.65rem;color:#90909e;text-transform:uppercase;letter-spacing:1px;">Emission Intensity (tCO₂e / GWh)</div>""", unsafe_allow_html=True)
            if a1_state_year:
                df_sy = pd.DataFrame(a1_state_year)
                df_sy["intensity"] = df_sy["total_emissions_tco2e"] / (df_sy["total_generation_mwh"] / 1000)
                df_int = df_sy.groupby("state")["intensity"].mean().sort_values(ascending=False)
                fig3 = go.Figure()
                fig3.add_trace(go.Bar(
                    x=df_int.index.tolist(),
                    y=df_int.values.tolist(),
                    marker_color=["#c62828", "#e65100", "#fdd835", "#2e7d32", "#1565c0", "#8e24aa", "#ff8f00", "#78909c"][:len(df_int)],
                ))
                fig3.update_layout(
                    paper_bgcolor="#f7f8fa", plot_bgcolor="#f7f8fa",
                    font=dict(color="#5a5a6e", size=10), showlegend=False,
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#e4e4ea"),
                    height=280,
                )
                st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
            else:
                st.caption("No data available")

        # ── Renewable Projects Map ──
        st.markdown("""<div style="font-size:0.65rem;color:#90909e;text-transform:uppercase;letter-spacing:1px;margin-top:10px;">Renewable Projects (Assignment 1 — Geocoded)</div>""", unsafe_allow_html=True)
        if a1_renewable:
            df_rp = pd.DataFrame(a1_renewable)
            fig_map = go.Figure()

            state_colors = {"NSW": "#636efa", "QLD": "#EF553B", "VIC": "#ab63fa",
                           "WA": "#00cc96", "SA": "#19d3f3", "ACT": "#FFA15A",
                           "TAS": "#FF6692", "NT": "#B6E880"}

            for st_name in sorted(df_rp["state"].unique()):
                sdf = df_rp[df_rp["state"] == st_name]
                fig_map.add_trace(go.Scattergeo(
                    lon=sdf["longitude"],
                    lat=sdf["latitude"],
                    mode="markers",
                    name=st_name,
                    marker=dict(
                        size=sdf["capacity_mw"].clip(lower=2).apply(lambda x: max(4, min(16, x / 30))),
                        color=state_colors.get(st_name, "#888"),
                        opacity=0.75,
                        line=dict(width=0.5, color="white"),
                    ),
                    text=sdf.apply(
                        lambda r: f"<b>{r['project_name']}</b><br>{r['capacity_mw']:.1f} MW • {r['fuel_source']} • {r['status']}",
                        axis=1,
                    ),
                    hoverinfo="text",
                ))

            fig_map.update_geos(
                scope="world",
                showcountries=True, countrycolor="lightgray",
                showcoastlines=True, coastlinecolor="gray",
                showland=True, landcolor="rgb(245,245,245)",
                showocean=True, oceancolor="rgb(230,240,255)",
                lataxis_range=[-45, -10], lonaxis_range=[110, 155],
                projection_type="mercator",
            )
            fig_map.update_layout(
                title="Geocoded Renewable Projects",
                paper_bgcolor="#f7f8fa",
                font=dict(color="#5a5a6e", size=10),
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", y=-0.1, font=dict(size=9)),
                height=400,
                title_font=dict(color="#1a1a24", size=11),
            )
            st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("No geocoded renewable project data available")

        # ── State-Year Data Table ──
        with st.expander("Integrated State-Year Data Table", expanded=False):
            if a1_state_year:
                df_table = pd.DataFrame(a1_state_year)
                df_table = df_table.rename(columns={
                    "state": "State", "year": "Year",
                    "total_generation_mwh": "Gen (MWh)",
                    "total_emissions_tco2e": "Emissions (tCO₂e)",
                    "total_businesses": "Businesses",
                    "small_businesses": "Small Biz",
                    "renewable_project_count": "Renew Projects",
                    "total_renewable_capacity_mw": "Renew Cap (MW)",
                })
                st.dataframe(df_table, use_container_width=True, hide_index=True)

        # ── Renewable Projects Table ──
        with st.expander("Renewable Projects Table (Geocoded)", expanded=False):
            if a1_renewable:
                df_rp2 = pd.DataFrame(a1_renewable)
                df_rp2 = df_rp2.rename(columns={
                    "project_name": "Project", "state": "State",
                    "capacity_mw": "MW", "fuel_source": "Fuel",
                    "status": "Status", "match_quality": "Match",
                })
                st.dataframe(
                    df_rp2[["Project", "State", "MW", "Fuel", "Status", "Match"]],
                    use_container_width=True, hide_index=True,
                )
