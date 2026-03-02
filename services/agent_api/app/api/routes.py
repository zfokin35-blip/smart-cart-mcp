from fastapi import APIRouter

from app.schemas.intent import IntentRequest, IntentResponse
from app.services.agent_factory import get_agent_service

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/intent", response_model=IntentResponse)
async def handle_intent(payload: IntentRequest):
    service = get_agent_service()
    result = await service.process_message(payload.user_id, payload.message)
    return IntentResponse(**result)
