"""
Data validation utilities.
"""
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum


class TransactionType(str, Enum):
    """Valid transaction types."""
    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    WITHDRAWAL = "WITHDRAWAL"
    DEPOSIT = "DEPOSIT"
    CONVERSION = "CONVERSION"


class TransactionStatus(str, Enum):
    """Valid transaction statuses."""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"


def validate_transaction(transaction: Dict[str, Any]) -> List[str]:
    """
    Validate a transaction record.
    
    Args:
        transaction: Transaction dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Required fields
    required_fields = [
        'transaction_id', 'from_account', 'to_account',
        'amount', 'transaction_type', 'timestamp'
    ]
    
    for field in required_fields:
        if field not in transaction:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return errors
    
    # Validate transaction_id (UUID format)
    if not is_valid_uuid(transaction.get('transaction_id')):
        errors.append("Invalid transaction_id format (must be UUID)")
    
    # Validate account IDs
    if not is_valid_account_id(transaction.get('from_account')):
        errors.append("Invalid from_account format")
    if not is_valid_account_id(transaction.get('to_account')):
        errors.append("Invalid to_account format")
    
    # Validate amount
    amount = transaction.get('amount')
    if not isinstance(amount, (int, float)) or amount <= 0:
        errors.append("Amount must be a positive number")
    
    # Validate transaction type
    try:
        TransactionType(transaction.get('transaction_type'))
    except ValueError:
        errors.append(f"Invalid transaction_type: {transaction.get('transaction_type')}")
    
    # Validate timestamp
    try:
        datetime.fromisoformat(transaction.get('timestamp'))
    except (ValueError, TypeError):
        errors.append("Invalid timestamp format (must be ISO format)")
    
    # Validate status if present
    if 'status' in transaction:
        try:
            TransactionStatus(transaction.get('status'))
        except ValueError:
            errors.append(f"Invalid status: {transaction.get('status')}")
    
    # Validate from_account != to_account
    if transaction.get('from_account') == transaction.get('to_account'):
        errors.append("from_account and to_account cannot be the same")
    
    return errors


def is_valid_uuid(value: str) -> bool:
    """Check if value is a valid UUID."""
    import uuid
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def is_valid_account_id(account_id: str) -> bool:
    """Check if account ID is in valid format."""
    # Accept alphanumeric account IDs of reasonable length
    if not isinstance(account_id, str):
        return False
    return bool(re.match(r'^[A-Z0-9]{8,20}$', account_id))


def is_valid_email(email: str) -> bool:
    """Check if email is valid."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_phone(phone: str) -> bool:
    """Check if phone number is valid."""
    # Allow various phone formats
    pattern = r'^\+?1?\d{9,15}$'
    return bool(re.match(pattern, phone.replace('-', '').replace(' ', '')))