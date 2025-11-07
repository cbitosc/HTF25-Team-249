import streamlit as st
import requests
import pandas as pd
import time
import pydeck as pdk
from datetime import datetime

# --- CONFIG ---
API_URL = "http://localhost:8000/api/status"
REFRESH_INTERVAL = 2  # seconds
MAX_HISTORY = 50
# --- Coordinates for our demo zones ---
ZONE_COORDS = {
    "gate_a": {"lat": 17.3871, "lon": 78.4917},
    "stage_front": {"lat": 17.3865, "lon": 78.4905},
}

# --- STREAMLIT PAGE SETTINGS ---
st.set_page_config(
    page_title="Crowd Safety Intelligence",
    page_icon="🚦",
    layout="wide",
)

# --- CSS for modern look ---
st.markdown(
    """
    <style>
    .big-title { font-size:36px; font-weight:800; color:#1E88E5; }
    /* Center-align metrics */
    div[data-testid="stMetric"] { text-align: center; }
    div[data-testid="stMetricLabel"] { font-size: 16px; }
    /* Style for the action box */
    .action-box { 
        padding: 10px; 
        border-radius: 10px; 
        background-color: #f0f2f6;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- STATE ---
if "history" not in st.session_state:
    st.session_state.history = {}
if "last_alert_count" not in st.session_state:
    st.session_state.last_alert_count = 0

# --- Helper function to fetch data ---
@st.cache_data(ttl=REFRESH_INTERVAL)
def get_status():
    try:
        res = requests.get(API_URL, timeout=1.5)
        if res.status_code == 200:
            return res.json()
    except requests.exceptions.RequestException:
        return None
    return None

# --- Function to add trend data ---
def update_trend(zone_id, density):
    if zone_id not in st.session_state.history:
        st.session_state.history[zone_id] = []
    st.session_state.history[zone_id].append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "density": density,
    })
    if len(st.session_state.history[zone_id]) > MAX_HISTORY:
        st.session_state.history[zone_id] = st.session_state.history[zone_id][-MAX_HISTORY:]

# ==============================================================================
# --- SIDEBAR ---
# ==============================================================================
with st.sidebar:
    st.title("🚦 Crowd Intel")
    st.caption("Crowd Safety Intelligence System")

    st.divider()
    st.subheader("System Status")
    status_indicator = st.empty()
    last_updated = st.empty()
    
    # --- ENHANCEMENT: High-Level Sidebar Metrics ---
    st.subheader("At-a-Glance")
    highest_risk_zone = st.empty()
    active_alerts_count = st.empty()
    
    st.divider()
    st.subheader("Risk Configuration")
    density_threshold = st.slider(
        "Set 'High Risk' Density Threshold (%)",
        min_value=0, max_value=100, value=80, step=5
    )
    threshold_float = density_threshold / 100.0
    st.caption("Adjust the visual 'High Risk' override.")

# ==============================================================================
# --- MAIN DASHBOARD ---
# ==============================================================================

st.markdown("<div class='big-title'>Live Command Center</div>", unsafe_allow_html=True)

# --- ENHANCEMENT: Tabs for better organization ---
tab_dashboard, tab_trends, tab_alerts = st.tabs([
    "📍 Live Dashboard", 
    "📈 Trend Analysis", 
    "🔔 Alert Log"
])

# --- Main container for live placeholders ---
dashboard_placeholder = tab_dashboard.empty()
trends_placeholder = tab_trends.empty()
alerts_placeholder = tab_alerts.empty()

while True:
    data = get_status()
    
    # --- Update Sidebar ---
    last_updated.caption(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")
    if data:
        status_indicator.success("● Connected to Backend", icon="✅")
    else:
        status_indicator.error("● Connection Lost", icon="❌")
        time.sleep(REFRESH_INTERVAL)
        continue

    zones = data.get("zones", [])
    alerts = data.get("alerts", [])

    # --- ENHANCEMENT: Show "Toast" for new alerts ---
    new_alert_count = len(alerts)
    if new_alert_count > st.session_state.last_alert_count:
        for a in alerts:
            st.toast(f"🚨 ALERT: {a['title']}", icon="🚨")
    st.session_state.last_alert_count = new_alert_count

    # --- Calculate high-level metrics ---
    highest_risk_zone_name = "None"
    if zones:
        highest_risk_zone_data = max(zones, key=lambda z: z['density'])
        highest_risk_zone_name = highest_risk_zone_data['display_name']
    
    highest_risk_zone.metric(label="Highest Risk Zone", value=highest_risk_zone_name)
    active_alerts_count.metric(label="Total Active Alerts", value=len(alerts))

    # ==========================================================================
    # --- TAB 1: LIVE DASHBOARD (Map, Cards, Actions) ---
    # ==========================================================================
    with dashboard_placeholder.container():
        
        # --- ENHANCEMENT: 2-Column Professional Layout ---
        col_map, col_info = st.columns([2, 1]) # 2/3 for map, 1/3 for info

        with col_map:
            st.subheader("🗺️ Live Density Heatmap")
            
            # --- Prep data for the map ---
            map_data_list = []
            for z in zones:
                coords = ZONE_COORDS.get(z["zone_id"], {"lat": 17.38, "lon": 78.49})
                map_data_list.append({
                    "lat": coords["lat"],
                    "lon": coords["lon"],
                    "density": z["density"],
                })
            map_data = pd.DataFrame(map_data_list)

            # --- ENHANCEMENT: 3D Hexagon Heatmap ---
            st.pydeck_chart(
                pdk.Deck(
                    map_style="mapbox://styles/mapbox/dark-v9",
                    initial_view_state=pdk.ViewState(
                        latitude=17.3868, 
                        longitude=78.4910, 
                        zoom=16, 
                        pitch=50 # 3D Angle
                    ),
                    layers=[
                        pdk.Layer(
                            "HexagonLayer",
                            data=map_data,
                            get_position="[lon, lat]",
                            get_elevation="density * 100", # Height of the bar
                            get_fill_color="[255, (1-density)*255, 0, 150]", # Red = high
                            radius=30,
                            elevation_scale=1,
                            elevation_range=[0, 100],
                            pickable=True,
                            extruded=True,
                        ),
                    ],
                    tooltip={"html": "<b>Density:</b> {elevationValue}%"}
                )
            )

        with col_info:
            st.subheader("📊 Zone Status")
            
            # --- ENHANCEMENT: Actionable Recommendations Box ---
            with st.container(border=True):
                st.subheader("💡 Recommended Actions")
                has_action = False
                for z in zones:
                    if z['density'] >= threshold_float:
                        st.warning(f"**Redirect flow** from {z['display_name']}.", icon="⚠️")
                        has_action = True
                if not has_action:
                    st.info("All zones stable. No actions required.", icon="✅")
            
            st.divider()

            # --- Zone KPI Cards ---
            for z in zones:
                density_pct = int(z['density'] * 100)
                update_trend(z["zone_id"], z["density"])

                # Check risk against the interactive slider
                if z['density'] >= threshold_float:
                    current_risk = "high"
                else:
                    current_risk = "medium" if z['density'] > (threshold_float / 2) else "low"
                
                trend_delta = None
                if z["trend"] == "up": trend_delta = "Increasing"
                elif z["trend"] == "down": trend_delta = "Decreasing"

                with st.container(border=True):
                    st.markdown(f"<h4 style='text-align: center;'>{z['display_name']}</h4>", unsafe_allow_html=True)
                    st.metric(
                        label="Risk",
                        value=current_risk.upper(),
                        delta=trend_delta,
                        delta_color=("inverse" if trend_delta == "Increasing" else "normal")
                    )
                    st.progress(z['density'], text=f"{density_pct}% Density")
                    st.markdown(f"**Predicted:** {z['predicted_risk_level'].capitalize()}")
                st.write("") # Add spacer

    # ==========================================================================
    # --- TAB 2: TREND ANALYSIS ---
    # ==========================================================================
    with trends_placeholder.container():
        st.subheader("Density Trends (Last 50 Updates)")
        chart_cols = st.columns(len(zones))
        
        for i, z in enumerate(zones):
            with chart_cols[i]:
                df = pd.DataFrame(st.session_state.history.get(z["zone_id"], []))
                st.markdown(f"**{z['display_name']}**")
                if not df.empty:
                    st.area_chart(df.set_index("time"), y="density", height=250, use_container_width=True)
                else:
                    st.info("No trend data yet.")

    # ==========================================================================
    # --- TAB 3: ALERT LOG ---
    # ==========================================================================
    with alerts_placeholder.container():
        st.subheader("Active Alerts Log")
        if alerts:
            for a in alerts:
                st.error(f"**[{a['zone_id'].upper()}] {a['title']}** - {a['message']}", icon="🚨")
        else:
            st.info("✅ No active alerts currently.")

    # --- Refresh ---
    time.sleep(REFRESH_INTERVAL)