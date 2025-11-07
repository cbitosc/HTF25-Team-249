from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any

# --- Ingestion (Person A -> Person B) ---

class CameraData(BaseModel):
    count: int

class IngestData(BaseModel):
    source_id: str
    source_type: str
    timestamp: datetime
    data: CameraData # We'll just handle camera data for now

# --- Status (Person B -> Frontend) ---

class ZoneStatus(BaseModel):
    zone_id: str
    display_name: str
    density: float         # 0.0 to 1.0
    risk_level: str        # 'low', 'medium', 'high', 'critical'
    predicted_risk_level: str # 'low', 'medium', 'high', 'critical'
    trend: str             # 'up', 'down', 'stable'

class Alert(BaseModel):
    id: str
    timestamp: datetime
    zone_id: str
    title: str
    message: str

class SystemStatus(BaseModel):
    zones: List[ZoneStatus]
    alerts: List[Alert]