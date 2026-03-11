import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_DATABASE = os.getenv("DB_DATABASE", "fraud_detection")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"

def init_db():
    print("INFO - Database engine created")
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                transaction_id VARCHAR(100) UNIQUE NOT NULL,
                from_account VARCHAR(100),
                to_account VARCHAR(100),
                amount DECIMAL(15,2),
                transaction_type VARCHAR(50),
                timestamp TIMESTAMP,
                risk_score DECIMAL(5,4),
                fraud_probability DECIMAL(5,4),
                aml_probability DECIMAL(5,4),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                alert_id VARCHAR(100) UNIQUE NOT NULL,
                transaction_id VARCHAR(100),
                alert_type VARCHAR(50),
                risk_score DECIMAL(5,4),
                severity VARCHAR(20),
                status VARCHAR(20) DEFAULT 'OPEN',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
    print("INFO - Database initialized successfully")

if __name__ == "__main__":
    init_db()
