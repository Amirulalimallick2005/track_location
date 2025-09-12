# # backend/utils.py
# import json
# from datetime import datetime
# from pathlib import Path

# LOG_DIR = Path(__file__).resolve().parents[0] / "logs"
# LOG_DIR.mkdir(parents=True, exist_ok=True)
# LOG_FILE = LOG_DIR / "tracking.log"

# def log_event(event: dict):
#     event['ts'] = datetime.utcnow().isoformat()
#     with open(LOG_FILE, 'a', encoding='utf-8') as f:
#         f.write(json.dumps(event, ensure_ascii=False) + "\n")
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL from environment variable
DATABASE_URL = os.environ.get("C:/Users/amiru/OneDrive/Documents/Desktop/SIH/backend/database")  # e.g., postgres://user:pass@host:port/dbname

# Setup SQLAlchemy
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Event table
class TrackingEvent(Base):
    __tablename__ = "tracking_events"
    id = Column(String, primary_key=True)  # could be UUID
    tourist_id = Column(String)
    event_type = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    result = Column(JSON)
    ts = Column(DateTime)

# Create table if not exists
Base.metadata.create_all(engine)

def log_event(event: dict):
    """
    Logs an event to the database.
    event should contain: tourist_id, event, latitude, longitude, result
    """
    event['ts'] = datetime.utcnow()
    session = Session()
    try:
        db_event = TrackingEvent(
            id=str(event.get("id") or event['ts'].timestamp()),  # simple unique id
            tourist_id=event.get("tourist_id"),
            event_type=event.get("event"),
            latitude=event.get("latitude"),
            longitude=event.get("longitude"),
            result=event.get("result"),
            ts=event['ts']
        )
        session.add(db_event)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Failed to log event to DB: {e}")
    finally:
        session.close()
