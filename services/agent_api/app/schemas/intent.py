from pydantic import BaseModel


class IntentRequest(BaseModel):
    user_id: str
    message: str
    session_id: str | None = None


class IntentResponse(BaseModel):
    reply: str
    actions: list[dict]
