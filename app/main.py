from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import movies, auth, users
from .database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Movie API",
    description="A comprehensive movie database API",
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
app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Movie API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}