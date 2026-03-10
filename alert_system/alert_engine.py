"""
Core alert generation engine.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    """Alert types."""
    FRAUD = "FRAUD"
    AML = "AML"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    THRESHOLD_BREACH = "THRESHOLD_BREACH"
    NETWORK_ANOMALY = "NETWORK_ANOMALY"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    """Alert statuses."""
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    CLOSED = "CLOSED"
    RESOLVED = "RESOLVED"


class AlertEngine:
    """Generates and manages alerts."""
    
    def __init__(self, db_manager=None, notifier=None):
        """
        Initialize alert engine.
        
        Args:
            db_manager: Database manager
            notifier: Alert notifier
        """
        self.db_manager = db_manager
        self.notifier = notifier
        self.alert_queue = []
    
    def create_alert(self, transaction_id: str, alert_type: AlertType,
                    risk_score: float, reason: str,
                    affected_accounts: List[str] = None,
                    additional_data: Dict = None) -> Dict[str, Any]:
        """
        Create a new alert.
        
        Args:
            transaction_id: Transaction ID
            alert_type: Type of alert
            risk_score: Risk score (0-1)
            reason: Alert reason
            affected_accounts: List of affected account IDs
            additional_data: Additional alert data
            
        Returns:
            Alert dictionary
        """
        alert_id = str(uuid.uuid4())
        severity = self._calculate_severity(risk_score)
        
        alert = {
            'alert_id': alert_id,
            'transaction_id': transaction_id,
            'alert_type': alert_type.value,
            'severity': severity.value,
            'risk_score': risk_score,
            'reason': reason,
            'affected_accounts': affected_accounts or [],
            'status': AlertStatus.OPEN.value,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'additional_data': additional_data or {}
        }
        
        logger.info(f"Created alert {alert_id} for transaction {transaction_id}")
        
        # Store in database if available
        if self.db_manager:
            self._store_alert(alert)
        
        # Send notification
        if self.notifier:
            self.notifier.send_alert(alert)
        
        return alert
    
    def _calculate_severity(self, risk_score: float) -> AlertSeverity:
        """Determine severity from risk score."""
        if risk_score >= 0.85:
            return AlertSeverity.CRITICAL
        elif risk_score >= 0.7:
            return AlertSeverity.HIGH
        elif risk_score >= 0.5:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    
    def _store_alert(self, alert: Dict) -> bool:
        """Store alert in database."""
        try:
            from database.models import Alert
            from sqlalchemy import insert
            
            session = self.db_manager.get_session()
            
            alert_record = Alert(
                alert_id=alert['alert_id'],
                transaction_id=alert['transaction_id'],
                alert_type=alert['alert_type'],
                risk_score=alert['risk_score'],
                reason=alert['reason'],
                affected_accounts=alert['affected_accounts']
            )
            
            session.add(alert_record)
            session.commit()
            session.close()
            
            return True
        except Exception as e:
            logger.error(f"Error storing alert: {str(e)}")
            return False
    
    def update_alert_status(self, alert_id: str, status: AlertStatus,
                           notes: str = None) -> bool:
        """
        Update alert status.
        
        Args:
            alert_id: Alert ID
            status: New status
            notes: Optional notes
            
        Returns:
            True if successful
        """
        try:
            if self.db_manager:
                from database.models import Alert
                
                session = self.db_manager.get_session()
                alert = session.query(Alert).filter(Alert.alert_id == alert_id).first()
                
                if alert:
                    alert.status = status.value
                    alert.updated_at = datetime.utcnow()
                    if notes:
                        alert.investigator_notes = notes
                    
                    session.commit()
                    session.close()
                    
                    logger.info(f"Updated alert {alert_id} status to {status.value}")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error updating alert: {str(e)}")
            return False
    
    def get_open_alerts(self, limit: int = 100) -> List[Dict]:
        """Get open alerts."""
        try:
            if self.db_manager:
                from database.models import Alert
                
                session = self.db_manager.get_session()
                alerts = session.query(Alert).filter(
                    Alert.status == AlertStatus.OPEN.value
                ).order_by(Alert.created_at.desc()).limit(limit).all()
                
                result = [
                    {
                        'alert_id': a.alert_id,
                        'transaction_id': a.transaction_id,
                        'alert_type': a.alert_type,
                        'risk_score': a.risk_score,
                        'reason': a.reason,
                        'created_at': a.created_at.isoformat()
                    }
                    for a in alerts
                ]
                
                session.close()
                return result
            
            return []
        except Exception as e:
            logger.error(f"Error fetching open alerts: {str(e)}")
            return []
    
    def get_alerts_by_type(self, alert_type: AlertType, limit: int = 100) -> List[Dict]:
        """Get alerts by type."""
        try:
            if self.db_manager:
                from database.models import Alert
                
                session = self.db_manager.get_session()
                alerts = session.query(Alert).filter(
                    Alert.alert_type == alert_type.value
                ).order_by(Alert.created_at.desc()).limit(limit).all()
                
                result = [
                    {
                        'alert_id': a.alert_id,
                        'transaction_id': a.transaction_id,
                        'risk_score': a.risk_score,
                        'status': a.status,
                        'created_at': a.created_at.isoformat()
                    }
                    for a in alerts
                ]
                
                session.close()
                return result
            
            return []
        except Exception as e:
            logger.error(f"Error fetching alerts by type: {str(e)}")
            return []