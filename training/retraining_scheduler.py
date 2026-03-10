"""
Automatic model retraining scheduler.
"""
import logging
import schedule # type: ignore
import time
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from database.models import Transaction, RetrainingLog
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetrainingScheduler:
    """Schedules and manages automatic model retraining."""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize scheduler."""
        self.db_manager = db_manager or DatabaseManager()
        self.interval_days = settings.models.retraining_interval_days
        self.min_samples = settings.models.min_samples_for_retraining
    
    def check_retraining_needed(self) -> bool:
        """Check if retraining is needed."""
        try:
            session = self.db_manager.get_session()
            
            # Check how many new transactions since last training
            cutoff_date = datetime.utcnow() - timedelta(days=self.interval_days)
            new_transactions = session.query(Transaction).filter(
                Transaction.processed_at >= cutoff_date
            ).count()
            
            session.close()
            
            logger.info(f"New transactions since last retraining: {new_transactions}")
            
            return new_transactions >= self.min_samples
        
        except Exception as e:
            logger.error(f"Error checking retraining needs: {str(e)}")
            return False
    
    def schedule_retraining(self):
        """Schedule automatic retraining."""
        logger.info("Scheduling automatic model retraining...")
        
        schedule.every(self.interval_days).days.do(self.trigger_retraining)
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    def trigger_retraining(self):
        """Trigger model retraining."""
        logger.info("Triggering model retraining...")
        
        try:
            # Train supervised model
            from training.train_supervised import train_supervised_model
            train_supervised_model()
            
            # Train unsupervised model
            from training.train_unsupervised import train_unsupervised_model
            train_unsupervised_model()
            
            # Log retraining event
            self._log_retraining_success()
            
            logger.info("Retraining completed successfully")
        
        except Exception as e:
            logger.error(f"Error during retraining: {str(e)}")
            self._log_retraining_failure(str(e))
    
    def _log_retraining_success(self):
        """Log successful retraining."""
        try:
            session = self.db_manager.get_session()
            
            log = RetrainingLog(
                model_name="ensemble",
                training_end=datetime.utcnow(),
                status="SUCCESS"
            )
            
            session.add(log)
            session.commit()
            session.close()
        except Exception as e:
            logger.error(f"Error logging retraining: {str(e)}")
    
    def _log_retraining_failure(self, error: str):
        """Log failed retraining."""
        try:
            session = self.db_manager.get_session()
            
            log = RetrainingLog(
                model_name="ensemble",
                training_end=datetime.utcnow(),
                status="FAILED",
                notes=error
            )
            
            session.add(log)
            session.commit()
            session.close()
        except Exception as e:
            logger.error(f"Error logging retraining failure: {str(e)}")