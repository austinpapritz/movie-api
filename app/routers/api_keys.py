# app/routers/api_keys.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import secrets
import string

from ..database import get_db
from ..models.api_key import APIKey
from ..schemas.api_key import APIKeyCreate, APIKeyResponse
from ..utils.admin import verify_admin_secret

router = APIRouter()

def generate_api_key() -> str:
    """Generate a simple API key"""
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    return f"sk_movie_{random_part}"

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_secret)  # 🔒 ADMIN ONLY
):
    """
    Create a new API key.
    
    **Admin only endpoint** - requires admin_secret query parameter.
    
    The generated API key will only be shown once in the response.
    Make sure to save it securely!
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


@router.get("/api-keys")
async def list_api_keys(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_secret)  # 🔒 ADMIN ONLY
):
    """
    List all API keys (without exposing the actual key values).
    
    **Admin only endpoint** - requires admin_secret query parameter.
    """
    
    api_keys = db.query(APIKey).order_by(APIKey.created_at.desc()).all()
    
    # Return info without exposing the actual keys
    return [
        {
            "id": key.id,
            "name": key.name,
            "is_active": key.is_active,
            "created_at": key.created_at,
            "key_preview": f"{key.key[:12]}..." if key.key else None  # Show first 12 chars only
        }
        for key in api_keys
    ]


@router.patch("/api-keys/{key_id}")
async def update_api_key(
    key_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_secret)  # 🔒 ADMIN ONLY
):
    """
    Activate or deactivate an API key.
    
    **Admin only endpoint** - requires admin_secret query parameter.
    """
    
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    api_key.is_active = is_active
    db.commit()
    
    status_text = "activated" if is_active else "deactivated"
    return {"message": f"API key '{api_key.name}' has been {status_text}"}


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_secret)  # 🔒 ADMIN ONLY
):
    """
    Permanently delete an API key.
    
    **Admin only endpoint** - requires admin_secret query parameter.
    """
    
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    key_name = api_key.name
    db.delete(api_key)
    db.commit()
    
    return {"message": f"API key '{key_name}' has been permanently deleted"}