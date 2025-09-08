import pytest

def test_root_endpoint(client):
    """Test that the root endpoint returns welcome message"""
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Movie API"}

def test_health_endpoint(client):
    """Test that the health check endpoint works"""
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_movies_endpoint_empty_db(client):
    """Test movies endpoint with empty database"""
    response = client.get("/api/v1/movies")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "movies" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    assert "pages" in data
    
    # Check empty database response
    assert data["movies"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["per_page"] == 20
    assert data["pages"] == 0

def test_movies_endpoint_with_data(client, sample_movies):
    """Test movies endpoint with sample data"""
    response = client.get("/api/v1/movies")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check we have data
    assert len(data["movies"]) == 3
    assert data["total"] == 3
    assert data["pages"] == 1
    
    # Check first movie structure
    first_movie = data["movies"][0]
    required_fields = ["id", "title", "overview", "vote_average", "budget", "revenue"]
    for field in required_fields:
        assert field in first_movie

def test_movies_endpoint_pagination(client, sample_movies):
    """Test pagination works correctly"""
    # Get first page with limit 2
    response = client.get("/api/v1/movies?page=1&limit=2")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["movies"]) == 2
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["per_page"] == 2
    assert data["pages"] == 2  # 3 movies / 2 per page = 2 pages
    
    # Get second page
    response = client.get("/api/v1/movies?page=2&limit=2")
    data = response.json()
    
    assert len(data["movies"]) == 1  # Only 1 movie left on page 2
    assert data["page"] == 2

def test_single_movie_endpoint(client, sample_movie):
    """Test getting a single movie by ID"""
    response = client.get(f"/api/v1/movies/{sample_movie.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == sample_movie.id
    assert data["title"] == sample_movie.title
    assert data["overview"] == sample_movie.overview

def test_single_movie_not_found(client):
    """Test 404 for non-existent movie"""
    response = client.get("/api/v1/movies/999")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

