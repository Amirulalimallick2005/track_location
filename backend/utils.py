
# backend/utils.py
import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[0] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "tracking.log"

def log_event(event: dict):
    event['ts'] = datetime.utcnow().isoformat()
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
