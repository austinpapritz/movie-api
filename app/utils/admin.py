# app/utils/admin.py
import os
import secrets
from fastapi import HTTPException, status, Query

async def verify_admin_secret(admin_secret: str = Query(..., description="Admin secret key")):
    """
    Simple admin authentication using environment variable.
    In production, replace with proper admin user authentication.
    """
    expected_secret = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    
    # Use secrets.compare_digest for timing attack protection
    if not secrets.compare_digest(admin_secret, expected_secret):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin secret"
        )
    return True