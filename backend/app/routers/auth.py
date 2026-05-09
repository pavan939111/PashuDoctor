from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: str
    user_id: str
    username: str

# Mock User DB
USERS = {
    "farmer123": "pashu2024",
    "admin": "admin123"
}

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Simple authentication for farmers.
    In a real app, this would use hashed passwords and JWT.
    """
    if request.username in USERS and USERS[request.username] == request.password:
        return LoginResponse(
            success=True,
            token=f"pd_token_{request.username}", # Mock token
            user_id=f"user_{request.username}",
            username=request.username
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password"
    )

@router.get("/validate")
async def validate_token(token: str):
    """
    Validate the mock token.
    """
    if token.startswith("pd_token_"):
        username = token.replace("pd_token_", "")
        if username in USERS:
            return {"valid": True, "username": username}
    
    return {"valid": False}
