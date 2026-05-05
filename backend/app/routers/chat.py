from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ChatMessage(BaseModel):
    message: str

@router.post("/chat")
async def chat(msg: ChatMessage):
    # Placeholder for chat logic
    return {"response": f"You said: {msg.message}"}
