import requests
import time
import datetime
import random
import json
import csv
import os

# --- Configuration ---
# This is the endpoint Person B is building.
# Make sure the port matches (e.g., 8000 for FastAPI).
INGEST_ENDPOINT = "http://localhost:8000/api/ingest"

# --- Prepare to log data for AI training ---
LOG_FILE = "crowd_data_log.csv"

# Create the CSV file with headers if it doesn’t exist
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "zone", "count"])

# --- Our Demo Scenario (The "Story") ---
# We will simulate 3 minutes of events, sped up.
#
# - 0-30 seconds:   Normal flow. (Gate A is busy but stable)
# - 30-60 seconds:  The Surge. (Gate A count climbs rapidly)
# - 60-90 seconds:  Critical Peak. (Gate A count is dangerously high)
# - 90-180 seconds: Recovery. (Crowd count slowly decreases)
#
# We'll run this loop every 2 seconds to simulate real-time data.

def get_crowd_count(simulation_time_sec):
    """
    Generates a crowd count based on our demo scenario.
    This function IS the "story".
    """
    # --- cam_01 (Main Gate A) ---
    if 0 <= simulation_time_sec < 30:
        count_gate_a = random.randint(80, 100)
    elif 30 <= simulation_time_sec < 60:
        base_count = 100 + (simulation_time_sec - 30) * 5  # (100 -> 250 in 30s)
        count_gate_a = int(base_count) + random.randint(-10, 10)
    elif 60 <= simulation_time_sec < 90:
        count_gate_a = random.randint(250, 300)
    else:
        base_count = 250 - (simulation_time_sec - 90) * 1.1  # (250 -> 151 in 90s)
        count_gate_a = max(150, int(base_count) + random.randint(-10, 10))

    # --- cam_02 (Stage Front) ---
    count_stage_front = random.randint(110, 130)

    return count_gate_a, count_stage_front


def send_data(source_id, count):
    """
    Formats and sends the data payload to the ingestion endpoint.
    """
    payload = {
        "source_id": source_id,
        "source_type": "camera",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "data": {"count": count},
    }

    try:
        response = requests.post(INGEST_ENDPOINT, json=payload, timeout=1.0)
        print(f"Sent: {source_id}, Count: {count}. Response: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"Error: Connection to {INGEST_ENDPOINT} refused. Is Person B's server running?")
    except requests.exceptions.RequestException as e:
        print(f"Error sending data: {e}")


# --- Main Simulation Loop ---
def run_simulation():
    print("--- Starting Crowd Safety Simulator ---")
    print(f"Sending data to: {INGEST_ENDPOINT}")

    start_time = time.time()

    while True:
        simulation_time = time.time() - start_time
        count_a, count_b = get_crowd_count(simulation_time)

        # Send the data to backend
        send_data("cam_01", count_a)  # Main Gate A
        send_data("cam_02", count_b)  # Stage Front

        # --- Log data locally for AI training ---
        with open(LOG_FILE, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.datetime.now().isoformat(), "gate_a", count_a])
            writer.writerow([datetime.datetime.now().isoformat(), "stage_front", count_b])

        # Restart simulation after 3 minutes
        if simulation_time > 180:
            print("--- Simulation complete (3 minutes elapsed) ---")
            start_time = time.time()

        time.sleep(2)


if __name__ == "__main__":
    run_simulation()
