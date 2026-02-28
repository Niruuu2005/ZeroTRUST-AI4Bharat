"""
Verification Router — POST /verify endpoint
"""
import logging
from fastapi import APIRouter, HTTPException
from src.models.verification import VerificationRequest, VerificationResult
from src.agents.manager import ManagerAgent

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize manager agent (singleton)
manager = ManagerAgent()


@router.post("", response_model=VerificationResult)
async def verify_claim(request: VerificationRequest):
    """
    Verify a claim using the multi-agent system.
    
    - **content**: The claim text, URL, or media reference
    - **type**: text | url | image | video
    - **source**: web_portal | extension | mobile_app | api
    - **user_id**: User identifier (default: anonymous)
    """
    try:
        logger.info(f"Verification request: type={request.type}, source={request.source}")
        result = await manager.verify(request)
        logger.info(f"Verification complete: score={result.credibility_score}, category={result.category}")
        return result
    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
