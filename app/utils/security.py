# app/utils/security.py
from fastapi import HTTPException, status, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.api_key import APIKey

# Set up the API key header
api_key_header = APIKeyHeader(
    name="X-API-Key",
    description="API key for authentication",
    auto_error=False,
)

async def validate_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> APIKey:
    """
    Simple API key validation.
    Returns the API key record if valid, raises 401 if not.
    """
    
    # Check if API key is provided
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Please provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKeyAuth"},
        )
    
    # Check if API key exists and is active
    db = next(get_db())
    try:
        db_api_key = db.query(APIKey).filter(
            APIKey.key == api_key,
            APIKey.is_active == True
        ).first()
        
        if not db_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive API key.",
                headers={"WWW-Authenticate": "ApiKeyAuth"},
            )
        
        return db_api_key
    
    finally:
        db.close()