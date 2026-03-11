import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_DATABASE = os.getenv("DB_DATABASE", "fraud_detection")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"

class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)

    def get_recent_transactions(self, limit=100):
        with self.engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM transactions ORDER BY created_at DESC LIMIT {limit}"))
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]

    def get_open_alerts(self, limit=50):
        with self.engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM alerts WHERE status='OPEN' ORDER BY created_at DESC LIMIT {limit}"))
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]

    def get_stats(self):
        with self.engine.connect() as conn:
            total = conn.execute(text("SELECT COUNT(*) FROM transactions")).scalar()
            alerts = conn.execute(text("SELECT COUNT(*) FROM alerts WHERE status='OPEN'")).scalar()
            high_risk = conn.execute(text("SELECT COUNT(*) FROM transactions WHERE risk_score > 0.7")).scalar()
            return {"total_transactions": total, "open_alerts": alerts, "high_risk": high_risk}
