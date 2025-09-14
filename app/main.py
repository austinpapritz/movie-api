from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import movies, api_keys
from .database import engine, Base
from .models import movie, api_key

# use `uvicorn app.main:app --reload` to run API
# use API at `http://localhost:8000/docs``

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Movie API",
    description="""
    A comprehensive movie database API with API key authentication.
    
    ## Authentication
    
    This API uses API key authentication. To get started:
    
    1. Get an admin secret key from your administrator
    2. Create an API key using `/api/v1/admin/api-keys/` endpoint
    3. Include the API key in the `X-API-Key` header for all 
    """,
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(movies.router, prefix="/api/v1", tags=["movies"])
app.include_router(api_keys.router, prefix="/api/v1/admin", tags=["admin"])
# app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
# app.include_router(users.router, prefix="/api/v1", tags=["users"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Movie API", 
        "docs": "/docs",
        "version": "1.0.0",
        "authentication": "API key required for most endpoints",
        "admin": "Use /api/v1/admin/api-keys/ to manage API keys"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}