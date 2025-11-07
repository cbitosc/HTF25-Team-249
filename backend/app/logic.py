from .schemas import IngestData, SystemStatus, ZoneStatus, Alert
from datetime import datetime
import numpy as np
import os
import joblib

# --- In-memory storage ---
current_counts = {}
density_history = {}  # For trend tracking (source_id -> list of counts)
MAX_HISTORY = 10

# --- Load trained ML model for prediction ---
MODEL_PATH = os.path.join(os.path.dirname(__file__), "crowd_predictor.pkl")
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    print(f"✅ Loaded ML model from {MODEL_PATH}")
else:
    model = None
    print(f"⚠️ ML model not found at {MODEL_PATH}, using trend-based prediction")

# --- Update counts ---
def process_new_data(data: IngestData):
    """
    Updates the current crowd counts and maintains recent history.
    """
    source = data.source_id
    count = data.data.count
    current_counts[source] = count

    # Maintain history
    if source not in density_history:
        density_history[source] = []
    density_history[source].append(count)
    if len(density_history[source]) > MAX_HISTORY:
        density_history[source] = density_history[source][-MAX_HISTORY:]


# --- Prediction logic ---
def predict_future_risk(zone_id: str, density: float) -> str:
    """
    Predict risk using ML model if available, else fallback to trend-based prediction.
    """
    # Use ML model for gate_a
    if model and zone_id == "cam_01":
        prev_count = density_history.get(zone_id, [])[-1] if density_history.get(zone_id) else 0
        predicted_count = model.predict([[prev_count]])[0]
        predicted_density = min(max(predicted_count / 200.0, 0.0), 1.0)
    else:
        # Trend-based fallback
        history = np.array(density_history.get(zone_id, []))
        if len(history) < 3:
            return "low"
        recent_trend = np.mean(np.diff(history[-3:]))
        predicted_density = min(max(density + (recent_trend / 200.0), 0.0), 1.0)

    # Determine risk level
    if predicted_density > 0.8:
        return "high"
    elif predicted_density > 0.5:
        return "medium"
    else:
        return "low"


def get_system_status() -> SystemStatus:
    """
    Returns live and predicted crowd status for all zones.
    """
    # Current counts
    gate_a_count = current_counts.get("cam_01", 0)
    stage_count = current_counts.get("cam_02", 0)

    # Convert to density
    density_a = min(gate_a_count / 200.0, 1.0)
    density_b = min(stage_count / 200.0, 1.0)

    # Risk mapping
    def get_risk(d):
        if d > 0.8:
            return "high"
        elif d > 0.5:
            return "medium"
        else:
            return "low"

    # Predicted risk
    predicted_risk_a = predict_future_risk("cam_01", density_a)
    predicted_risk_b = predict_future_risk("cam_02", density_b)

    # Trend calculation for UI
    def get_trend(source_id):
        hist = density_history.get(source_id, [])
        if len(hist) < 3:
            return "stable"
        diff = np.mean(np.diff(hist[-3:]))
        if diff > 2:
            return "up"
        elif diff < -2:
            return "down"
        else:
            return "stable"

    zone1 = ZoneStatus(
        zone_id="gate_a",
        display_name="Main Gate A",
        density=density_a,
        risk_level=get_risk(density_a),
        predicted_risk_level=predicted_risk_a,
        trend=get_trend("cam_01"),
    )

    zone2 = ZoneStatus(
        zone_id="stage_front",
        display_name="Stage Front",
        density=density_b,
        risk_level=get_risk(density_b),
        predicted_risk_level=predicted_risk_b,
        trend=get_trend("cam_02"),
    )

    # Alerts if risk high
    alerts = []
    if zone1.risk_level == "high":
        alerts.append(Alert(
            id="alert_1",
            timestamp=datetime.utcnow(),
            zone_id="gate_a",
            title="⚠️ High Risk at Main Gate A",
            message="Crowd density critical. Please redirect flow."
        ))

    if zone2.risk_level == "high":
        alerts.append(Alert(
            id="alert_2",
            timestamp=datetime.utcnow(),
            zone_id="stage_front",
            title="⚠️ High Risk at Stage Front",
            message="High density detected. Manage access routes."
        ))

    return SystemStatus(zones=[zone1, zone2], alerts=alerts)
