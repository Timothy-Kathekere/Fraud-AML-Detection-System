"""
Dashboard data endpoints.
"""
import logging
from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)
router = APIRouter()

db_manager = DatabaseManager()


@router.get("/dashboard/metrics")
async def get_dashboard_metrics():
    """Get dashboard metrics and KPIs."""
    try:
        from database.models import Transaction, Alert
        
        session = db_manager.get_session()
        
        # 24-hour metrics
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Total transactions
        total_txns_24h = session.query(Transaction).filter(
            Transaction.timestamp >= cutoff_time
        ).count()
        
        # Fraud detections
        fraud_detections = session.query(Transaction).filter(
            Transaction.fraud_score >= 0.6,
            Transaction.timestamp >= cutoff_time
        ).count()
        
        # AML alerts
        aml_alerts = session.query(Alert).filter(
            Alert.alert_type == "AML",
            Alert.created_at >= cutoff_time
        ).count()
        
        # Average fraud score
        avg_fraud_score = session.query(
            func.avg(Transaction.fraud_score) # type: ignore
        ).filter(
            Transaction.timestamp >= cutoff_time
        ).scalar() or 0
        
        session.close()
        
        return {
            "total_transactions_24h": total_txns_24h,
            "fraud_detections_24h": fraud_detections,
            "aml_alerts_24h": aml_alerts,
            "avg_fraud_score": avg_fraud_score,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {str(e)}")
        return {"error": str(e)}


@router.get("/dashboard/alerts-timeline")
async def get_alerts_timeline(hours: int = Query(24, le=168)):
    """Get alert timeline for last N hours."""
    try:
        from database.models import Alert
        import pandas as pd
        
        session = db_manager.get_session()
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        alerts = session.query(Alert).filter(
            Alert.created_at >= cutoff_time
        ).all()
        
        # Group by hour
        timeline_data = {}
        for alert in alerts:
            hour_key = alert.created_at.strftime("%Y-%m-%d %H:00")
            timeline_data[hour_key] = timeline_data.get(hour_key, 0) + 1
        
        session.close()
        
        return {
            "timeline": timeline_data,
            "total_alerts": len(alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting timeline: {str(e)}")
        return {"error": str(e)}