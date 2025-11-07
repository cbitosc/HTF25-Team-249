from fastapi import FastAPI
from . import schemas, logic

app = FastAPI()

@app.post("/api/ingest")
def post_ingest_data(data: schemas.IngestData):
    """
    Receives data from Person A (simulator)
    """
    logic.process_new_data(data)
    return {"status": "ok", "source_id": data.source_id}

@app.get("/api/status", response_model=schemas.SystemStatus)
def get_status():
    """
    Provides data to the Frontend (Person C)
    """
    return logic.get_system_status()