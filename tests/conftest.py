# tests/conftest.py
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db, Base
from app.models.movie import Movie

# Test database configuration
TEST_DATABASE_URL = "sqlite:///:memory:"  # In-memory database

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Keep connection alive for in-memory DB
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Override the database dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine for the entire test session"""
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    # In-memory database automatically cleans up

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a fresh database session for each test"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with overridden database"""
    def override_get_db_for_testing():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db_for_testing

    with TestClient(app) as test_client:
        yield test_client

    # Clean up dependency override
    app.dependency_overrides.clear()

@pytest.fixture
def sample_movie(db_session):
    """Create a sample movie for testing"""
    from datetime import date

    movie = Movie(
        id=1,
        title="Test Movie",
        original_title="Test Movie",
        overview="A test movie for testing purposes",
        release_date=date(2023, 1, 1),
        runtime=120.0,
        budget=1000000,
        revenue=2000000,
        vote_average=7.5,
        vote_count=100,
        popularity=10.0,
        adult=False,
        video=False,
        status="Released",
        original_language="en"
    )
    db_session.add(movie)
    db_session.commit()
    db_session.refresh(movie)
    return movie

@pytest.fixture
def sample_movies(db_session):
    """Create multiple sample movies for pagination/filtering tests"""
    movies = [
        Movie(
            id=1,
            title="Action Movie",
            overview="An action-packed film",
            vote_average=8.0,
            vote_count=200,
            budget=50000000,
            revenue=150000000,
            popularity=20.0,
            original_language="en",
            status="Released"
        ),
        Movie(
            id=2, 
            title="Comedy Movie",
            overview="A funny film",
            vote_average=6.5,
            vote_count=150,
            budget=20000000,
            revenue=80000000,
            popularity=15.0,
            original_language="en",
            status="Released"
        ),
        Movie(
            id=3,
            title="Drama Movie", 
            overview="A dramatic film",
            vote_average=9.0,
            vote_count=300,
            budget=30000000,
            revenue=120000000,
            popularity=25.0,
            original_language="en",
            status="Released"
        )
    ]

    for movie in movies:
        db_session.add(movie)
    db_session.commit()

    return movies