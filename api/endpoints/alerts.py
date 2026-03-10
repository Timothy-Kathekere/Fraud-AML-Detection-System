"""
Alert management endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import datetime
from alert_system.alert_engine import AlertEngine, AlertType

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize alert engine (would be dependency injected)
alert_engine = AlertEngine()


@router.get("/alerts/open")
async def get_open_alerts(limit: int = Query(100, le=1000)):
    """Get open alerts."""
    try:
        alerts = alert_engine.get_open_alerts(limit=limit)
        return {
            "count": len(alerts),
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching open alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/by-type/{alert_type}")
async def get_alerts_by_type(alert_type: str, limit: int = Query(100, le=1000)):
    """Get alerts by type."""
    try:
        alert_type_enum = AlertType[alert_type.upper()]
        alerts = alert_engine.get_alerts_by_type(alert_type_enum, limit=limit)
        
        return {
            "alert_type": alert_type,
            "count": len(alerts),
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat()
        }
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid alert type: {alert_type}")
    except Exception as e:
        logger.error(f"Error fetching alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/alerts/{alert_id}/status")
async def update_alert_status(alert_id: str, status: str, notes: str = None):
    """Update alert status."""
    try:
        from alert_system.alert_engine import AlertStatus
        
        status_enum = AlertStatus[status.upper()]
        success = alert_engine.update_alert_status(alert_id, status_enum, notes)
        
        if success:
            return {
                "alert_id": alert_id,
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    except Exception as e:
        logger.error(f"Error updating alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))