"""
Case management system for investigation tracking.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class CaseManager:
    """Manages investigation cases."""
    
    def __init__(self, db_manager=None):
        """
        Initialize case manager.
        
        Args:
            db_manager: Database manager
        """
        self.db_manager = db_manager
    
    def create_case(self, case_type: str, primary_account: str,
                   related_accounts: List[str] = None,
                   priority: str = "MEDIUM",
                   description: str = None) -> Dict[str, any]:
        """
        Create a new investigation case.
        
        Args:
            case_type: Type of case (FRAUD, AML, SUSPICIOUS_ACTIVITY)
            primary_account: Primary account involved
            related_accounts: Related accounts
            priority: Case priority (LOW, MEDIUM, HIGH, CRITICAL)
            description: Case description
            
        Returns:
            Case dictionary
        """
        case_id = str(uuid.uuid4())
        
        case = {
            'case_id': case_id,
            'case_type': case_type,
            'primary_account': primary_account,
            'related_accounts': related_accounts or [],
            'priority': priority,
            'status': 'OPEN',
            'description': description,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
        }
        
        # Store in database
        if self.db_manager:
            self._store_case(case)
        
        logger.info(f"Created case {case_id} ({case_type})")
        return case
    
    def _store_case(self, case: Dict) -> bool:
        """Store case in database."""
        try:
            from database.models import Case
            
            session = self.db_manager.get_session()
            
            case_record = Case(
                case_id=case['case_id'],
                case_type=case['case_type'],
                primary_account=case['primary_account'],
                related_accounts=case['related_accounts'],
                priority=case['priority'],
                description=case['description']
            )
            
            session.add(case_record)
            session.commit()
            session.close()
            
            return True
        except Exception as e:
            logger.error(f"Error storing case: {str(e)}")
            return False
    
    def link_alert_to_case(self, alert_id: str, case_id: str) -> bool:
        """Link an alert to a case."""
        try:
            if self.db_manager:
                from database.models import Alert
                
                session = self.db_manager.get_session()
                alert = session.query(Alert).filter(Alert.alert_id == alert_id).first()
                
                if alert:
                    alert.case_id = case_id
                    session.commit()
                    session.close()
                    
                    logger.info(f"Linked alert {alert_id} to case {case_id}")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error linking alert to case: {str(e)}")
            return False
    
    def get_case(self, case_id: str) -> Optional[Dict]:
        """Get case details."""
        try:
            if self.db_manager:
                from database.models import Case
                
                session = self.db_manager.get_session()
                case = session.query(Case).filter(Case.case_id == case_id).first()
                
                if case:
                    result = {
                        'case_id': case.case_id,
                        'case_type': case.case_type,
                        'primary_account': case.primary_account,
                        'related_accounts': case.related_accounts,
                        'status': case.status,
                        'priority': case.priority,
                        'assigned_to': case.assigned_to,
                        'description': case.description,
                        'findings': case.findings,
                        'created_at': case.created_at.isoformat() if case.created_at else None,
                        'updated_at': case.updated_at.isoformat() if case.updated_at else None,
                    }
                    
                    session.close()
                    return result
            
            return None
        except Exception as e:
            logger.error(f"Error getting case: {str(e)}")
            return None
    
    def get_open_cases(self, limit: int = 50) -> List[Dict]:
        """Get open cases."""
        try:
            if self.db_manager:
                from database.models import Case
                
                session = self.db_manager.get_session()
                cases = session.query(Case).filter(
                    Case.status == "OPEN"
                ).order_by(Case.priority).limit(limit).all()
                
                result = [
                    {
                        'case_id': c.case_id,
                        'case_type': c.case_type,
                        'primary_account': c.primary_account,
                        'priority': c.priority,
                        'created_at': c.created_at.isoformat()
                    }
                    for c in cases
                ]
                
                session.close()
                return result
            
            return []
        except Exception as e:
            logger.error(f"Error getting open cases: {str(e)}")
            return []
    
    def close_case(self, case_id: str, resolution: str, findings: Dict = None) -> bool:
        """Close an investigation case."""
        try:
            if self.db_manager:
                from database.models import Case
                
                session = self.db_manager.get_session()
                case = session.query(Case).filter(Case.case_id == case_id).first()
                
                if case:
                    case.status = "CLOSED"
                    case.closed_at = datetime.utcnow()
                    case.resolution = resolution
                    case.findings = findings
                    case.updated_at = datetime.utcnow()
                    
                    session.commit()
                    session.close()
                    
                    logger.info(f"Closed case {case_id}")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error closing case: {str(e)}")
            return False