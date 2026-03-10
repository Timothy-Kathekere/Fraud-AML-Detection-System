"""
Batch scoring endpoint.
"""
import logging
from fastapi import APIRouter, HTTPException
from typing import List
import time
import uuid
from api.schemas import BatchScoringRequest, BatchScoringResponse, TransactionResponse
from api.endpoints.score import score_transaction

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/batch", response_model=BatchScoringResponse)
async def batch_score(request: BatchScoringRequest):
    """
    Score a batch of transactions.
    
    Processes transactions in parallel for maximum throughput.
    """
    start_time = time.time()
    batch_id = str(uuid.uuid4())
    
    try:
        results = []
        failed_count = 0
        high_risk_count = 0
        
        for transaction in request.transactions:
            try:
                result = await score_transaction(transaction)
                results.append(result)
                
                if result.risk_level in ["HIGH", "CRITICAL"]:
                    high_risk_count += 1
            
            except Exception as e:
                logger.error(f"Error scoring transaction {transaction.transaction_id}: {str(e)}")
                failed_count += 1
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return BatchScoringResponse(
            batch_id=batch_id,
            total_transactions=len(request.transactions),
            processed_transactions=len(results),
            failed_transactions=failed_count,
            high_risk_count=high_risk_count,
            processing_time_ms=processing_time_ms,
            results=results if request.include_details else None
        )
    
    except Exception as e:
        logger.error(f"Error in batch scoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))