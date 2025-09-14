# app/routers/api_keys.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import secrets
import string

from ..database import get_db
from ..models.api_key import APIKey
from ..schemas.api_key import APIKeyCreate, APIKeyResponse

router = APIRouter()

def generate_api_key() -> str:
    """Generate a simple API key"""
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    return f"sk_movie_{random_part}"

@router.post("/api-keys")  # Removed response_model temporarily
async def create_api_key(
    key_data: APIKeyCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new API key.
    
    For now, this is open - anyone can create a key.
    We'll add admin protection in the next step.
    """
    
    # Check if name already exists
    existing_key = db.query(APIKey).filter(APIKey.name == key_data.name).first()
    if existing_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"API key with name '{key_data.name}' already exists"
        )
    
    # Generate the actual API key
    api_key_value = generate_api_key()
    
    # Create new API key record
    db_api_key = APIKey(
        key=api_key_value,
        name=key_data.name
    )
    
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    return APIKeyResponse.model_validate(db_api_key)