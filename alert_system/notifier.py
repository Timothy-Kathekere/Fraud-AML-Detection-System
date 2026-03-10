"""
Alert notification system for email, Slack, webhooks.
"""
import logging
import json
from typing import Dict, Any, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests # type: ignore
from config.settings import settings

logger = logging.getLogger(__name__)


class AlertNotifier:
    """Sends alerts via multiple channels."""
    
    def __init__(self):
        """Initialize notifier."""
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
    
    def send_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Send alert through configured channels.
        
        Args:
            alert: Alert dictionary
            
        Returns:
            True if successful
        """
        success = True
        
        if settings.alerts.send_email_alerts:
            if not self._send_email(alert):
                success = False
        
        if settings.alerts.send_slack_alerts:
            if not self._send_slack(alert):
                success = False
        
        if settings.alerts.send_webhook_alerts:
            if not self._send_webhook(alert):
                success = False
        
        return success
    
    def _send_email(self, alert: Dict[str, Any]) -> bool:
        """Send email alert."""
        try:
            subject = f"[{alert['severity']}] {alert['alert_type']} Alert"
            
            body = f"""
            Alert ID: {alert['alert_id']}
            Transaction ID: {alert['transaction_id']}
            Type: {alert['alert_type']}
            Severity: {alert['severity']}
            Risk Score: {alert['risk_score']:.2%}
            Reason: {alert['reason']}
            Affected Accounts: {', '.join(alert.get('affected_accounts', []))}
            Time: {alert['created_at']}
            """
            
            msg = MIMEMultipart()
            msg['From'] = "alerts@frauddetection.local"
            msg['To'] = ", ".join(settings.alerts.email_recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # In production, connect to actual SMTP server
            logger.info(f"Email alert would be sent to {settings.alerts.email_recipients}")
            
            return True
        except Exception as e:
            logger.error(f"Error sending email alert: {str(e)}")
            return False
    
    def _send_slack(self, alert: Dict[str, Any]) -> bool:
        """Send Slack alert."""
        try:
            if not settings.alerts.slack_webhook_url:
                logger.warning("Slack webhook URL not configured")
                return False
            
            severity_color = {
                "CRITICAL": "#FF0000",
                "HIGH": "#FF6600",
                "MEDIUM": "#FFCC00",
                "LOW": "#00CC00"
            }
            
            color = severity_color.get(alert['severity'], "#808080")
            
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"{alert['alert_type']} Alert - {alert['severity']}",
                        "fields": [
                            {
                                "title": "Alert ID",
                                "value": alert['alert_id'],
                                "short": True
                            },
                            {
                                "title": "Transaction ID",
                                "value": alert['transaction_id'],
                                "short": True
                            },
                            {
                                "title": "Risk Score",
                                "value": f"{alert['risk_score']:.2%}",
                                "short": True
                            },
                            {
                                "title": "Reason",
                                "value": alert['reason'],
                                "short": False
                            },
                            {
                                "title": "Affected Accounts",
                                "value": ", ".join(alert.get('affected_accounts', [])),
                                "short": False
                            }
                        ],
                        "ts": int(__import__('datetime').datetime.utcnow().timestamp())
                    }
                ]
            }
            
            response = requests.post(
                settings.alerts.slack_webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Slack alert sent for {alert['alert_id']}")
                return True
            else:
                logger.error(f"Slack alert failed with status {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Error sending Slack alert: {str(e)}")
            return False
    
    def _send_webhook(self, alert: Dict[str, Any]) -> bool:
        """Send webhook alert."""
        try:
            if not settings.alerts.webhook_url:
                logger.warning("Webhook URL not configured")
                return False
            
            response = requests.post(
                settings.alerts.webhook_url,
                json=alert,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Webhook alert sent for {alert['alert_id']}")
                return True
            else:
                logger.error(f"Webhook alert failed with status {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Error sending webhook alert: {str(e)}")
            return False