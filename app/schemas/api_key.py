# app/schemas/api_key.py
from pydantic import BaseModel
from datetime import datetime

class APIKeyCreate(BaseModel):
    name: str

class APIKeyResponse(BaseModel):
    id: int
    key: str
    name: str
    is_active: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}