"""
Rule definitions for alert triggering.
"""
import logging
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class AlertRule:
    """Alert rule definition."""
    rule_id: str
    rule_name: str
    condition_type: str  # threshold, pattern, anomaly
    parameter: str  # Feature to check
    operator: str  # >, <, ==, >=, <=, in
    threshold: Any
    alert_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL


class AlertRuleEngine:
    """Evaluates alert rules."""
    
    def __init__(self):
        """Initialize rule engine."""
        self.rules = self._initialize_rules()
    
    def _initialize_rules(self) -> List[AlertRule]:
        """Initialize default alert rules."""
        return [
            # Fraud detection rules
            AlertRule(
                rule_id="fraud_high_risk",
                rule_name="High Risk Fraud Score",
                condition_type="threshold",
                parameter="fraud_probability",
                operator=">=",
                threshold=0.8,
                alert_type="FRAUD",
                severity="CRITICAL"
            ),
            
            AlertRule(
                rule_id="fraud_medium_risk",
                rule_name="Medium Risk Fraud Score",
                condition_type="threshold",
                parameter="fraud_probability",
                operator=">=",
                threshold=0.6,
                alert_type="FRAUD",
                severity="HIGH"
            ),
            
            # AML detection rules
            AlertRule(
                rule_id="aml_high_risk",
                rule_name="High Risk AML Score",
                condition_type="threshold",
                parameter="aml_probability",
                operator=">=",
                threshold=0.8,
                alert_type="AML",
                severity="CRITICAL"
            ),
            
            AlertRule(
                rule_id="circular_transaction",
                rule_name="Circular Transaction Detected",
                condition_type="pattern",
                parameter="circular_flow_likelihood",
                operator=">=",
                threshold=0.7,
                alert_type="AML",
                severity="HIGH"
            ),
            
            # Velocity rules
            AlertRule(
                rule_id="high_velocity",
                rule_name="High Transaction Velocity",
                condition_type="threshold",
                parameter="velocity_1h_count",
                operator=">=",
                threshold=10,
                alert_type="SUSPICIOUS_ACTIVITY",
                severity="MEDIUM"
            ),
            
            # Amount rules
            AlertRule(
                rule_id="large_amount",
                rule_name="Large Transaction Amount",
                condition_type="threshold",
                parameter="amount",
                operator=">=",
                threshold=100000,
                alert_type="THRESHOLD_BREACH",
                severity="MEDIUM"
            ),
            
            # Network rules
            AlertRule(
                rule_id="hub_account_transaction",
                rule_name="Transaction from Hub Account",
                condition_type="pattern",
                parameter="graph_degree_centrality",
                operator=">=",
                threshold=0.3,
                alert_type="NETWORK_ANOMALY",
                severity="LOW"
            ),
            
            # Geography rules
            AlertRule(
                rule_id="high_risk_jurisdiction",
                rule_name="High Risk Jurisdiction",
                condition_type="pattern",
                parameter="is_high_risk_jurisdiction",
                operator="==",
                threshold=1,
                alert_type="SUSPICIOUS_ACTIVITY",
                severity="MEDIUM"
            ),
            
            # Anomaly rules
            AlertRule(
                rule_id="statistical_anomaly",
                rule_name="Statistical Anomaly Detected",
                condition_type="anomaly",
                parameter="anomaly_probability",
                operator=">=",
                threshold=0.75,
                alert_type="SUSPICIOUS_ACTIVITY",
                severity="MEDIUM"
            ),
        ]
    
    def evaluate_rules(self, transaction_features: Dict[str, Any]) -> List[Dict]:
        """
        Evaluate all rules against transaction features.
        
        Args:
            transaction_features: Dictionary of transaction features
            
        Returns:
            List of triggered rules
        """
        triggered_rules = []
        
        for rule in self.rules:
            if self._evaluate_rule(rule, transaction_features):
                triggered_rules.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'alert_type': rule.alert_type,
                    'severity': rule.severity
                })
        
        return triggered_rules
    
    def _evaluate_rule(self, rule: AlertRule, features: Dict[str, Any]) -> bool:
        """Evaluate a single rule."""
        if rule.parameter not in features:
            return False
        
        value = features[rule.parameter]
        
        if rule.operator == ">=":
            return value >= rule.threshold
        elif rule.operator == ">":
            return value > rule.threshold
        elif rule.operator == "<=":
            return value <= rule.threshold
        elif rule.operator == "<":
            return value < rule.threshold
        elif rule.operator == "==":
            return value == rule.threshold
        elif rule.operator == "!=":
            return value != rule.threshold
        elif rule.operator == "in":
            return value in rule.threshold
        
        return False
    
    def add_rule(self, rule: AlertRule) -> bool:
        """Add a new rule."""
        self.rules.append(rule)
        logger.info(f"Added rule: {rule.rule_name}")
        return True
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID."""
        self.rules = [r for r in self.rules if r.rule_id != rule_id]
        logger.info(f"Removed rule: {rule_id}")
        return True
    
    def get_rules(self) -> List[AlertRule]:
        """Get all rules."""
        return self.rules