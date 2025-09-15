# app/routers/movies.py
from fastapi import APIRouter, Depends, HTTPException, Query, Response, Security
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import Optional, List
import math

from ..database import get_db
from ..models.movie import Movie
from ..models.api_key import APIKey
from ..schemas.movie import MovieResponse, MovieListResponse
from ..utils.security import validate_api_key

router = APIRouter()
@router.get("/movies/{movie_id}", response_model=MovieResponse)
async def get_movie(movie_id: int, db: Session = Depends(get_db), api_key: APIKey = Security(validate_api_key)):  # 🔑 API KEY REQUIRED)
    movie = db.query(Movie).filter(Movie.id == movie_id).first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

      # Extract values first to avoid SQLAlchemy column issues
    budget = getattr(movie, 'budget', None)
    revenue = getattr(movie, 'revenue', None)

    # Calculate profit margin
    profit_margin = None
    if budget and revenue and budget > 0 and revenue > 0:
        profit_margin = round(((revenue - budget) / budget) * 100, 2)

    movie_dict = {
    "id": movie.id,
    "title": movie.title,
    "original_title": movie.original_title,
    "overview": movie.overview,
    "release_date": movie.release_date,
    "runtime": movie.runtime,
    "vote_average": movie.vote_average,
    "vote_count": movie.vote_count,
    "popularity": movie.popularity,
    "budget": movie.budget,
    "revenue": movie.revenue,
    "poster_path": movie.poster_path,
    "imdb_id": movie.imdb_id,
    "genres": movie.genres,
    "profit_margin": profit_margin
}

    return MovieResponse(**movie_dict)

@router.get("/movies", response_model=MovieListResponse)
async def get_movies(
    response: Response,
    # Pagination parameters
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(20, ge=1, le=100, description="Number of movies per page"),
    
    # Filter parameters
    genre: Optional[str] = Query(None, description="Filter by genre (e.g., 'Action', 'Comedy')"),
    min_rating: Optional[float] = Query(None, ge=0, le=10, description="Minimum vote average"),
    max_rating: Optional[float] = Query(None, ge=0, le=10, description="Maximum vote average"),
    year: Optional[int] = Query(None, ge=1900, le=2030, description="Release year"),
    min_budget: Optional[int] = Query(None, ge=0, description="Minimum budget in dollars"),
    max_budget: Optional[int] = Query(None, ge=0, description="Maximum budget in dollars"),
    language: Optional[str] = Query(None, description="Original language (e.g., 'en', 'fr', 'es')"),
    
    # Search parameter
    search: Optional[str] = Query(None, min_length=2, description="Search in movie titles and overviews"),
    
    # Sort parameters
    sort_by: str = Query(
        "popularity", 
        pattern="^(popularity|vote_average|release_date|revenue|budget|title|vote_count)$",
        description="Field to sort by"
    ),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    
    # Dependencies
    db: Session = Depends(get_db),
    api_key: APIKey = Security(validate_api_key)  # 🔑 API KEY REQUIRED
):
    """
    Get movies with comprehensive filtering, sorting, and pagination.
    
    **Requires API key authentication.**
    
    This endpoint demonstrates:
    - Complex query building with multiple filters
    - Pagination with page/limit
    - Dynamic sorting 
    - Full-text search
    - Data transformation (profit calculations)
    - Rate limiting per API key
    """
    
    # Start with base query
    query = db.query(Movie)
    
    # Build filters list (we'll combine with AND)
    filters = []
    
    # Genre filter - search in JSON array
    if genre:
        # This searches for the genre name within the JSON genres field
        filters.append(Movie.genres.like(f'%"name": "{genre}"%'))
    
    # Rating filters
    if min_rating is not None:
        filters.append(Movie.vote_average >= min_rating)
    if max_rating is not None:
        filters.append(Movie.vote_average <= max_rating)
    
    # Year filter - extract year from release_date
    if year:
        filters.append(func.strftime('%Y', Movie.release_date) == str(year))
    
    # Budget filters
    if min_budget is not None:
        filters.append(Movie.budget >= min_budget)
    if max_budget is not None:
        filters.append(Movie.budget <= max_budget)
    
    # Language filter
    if language:
        filters.append(Movie.original_language == language)
    
    # Search filter - looks in title, original_title, and overview
    if search:
        search_term = f"%{search.lower()}%"
        search_conditions = or_(
            func.lower(Movie.title).like(search_term),
            func.lower(Movie.original_title).like(search_term),
            func.lower(Movie.overview).like(search_term)
        )
        filters.append(search_conditions)
    
    # Apply all filters
    if filters:
        query = query.filter(and_(*filters))
    
    # Apply sorting
    sort_column = getattr(Movie, sort_by)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Get total count for pagination info (before applying limit/offset)
    total_count = query.count()
    
    # Calculate pagination
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 0
    offset = (page - 1) * limit
    
    # Apply pagination and execute query
    movies = query.offset(offset).limit(limit).all()
    
    # Transform movies with calculated fields
    movie_responses = []
    for movie in movies:
        # Calculate profit margin if we have budget and revenue data
        profit_margin = None
        if movie.budget and movie.budget > 0 and movie.revenue and movie.revenue > 0:
            profit_margin = round(((movie.revenue - movie.budget) / movie.budget) * 100, 2)
        
        # Create response object with all movie data plus calculated fields
        movie_dict = {
            "id": movie.id,
            "title": movie.title,
            "original_title": movie.original_title,
            "overview": movie.overview,
            "release_date": movie.release_date,
            "runtime": movie.runtime,
            "vote_average": movie.vote_average,
            "vote_count": movie.vote_count,
            "popularity": movie.popularity,
            "budget": movie.budget,
            "revenue": movie.revenue,
            "poster_path": movie.poster_path,
            "imdb_id": movie.imdb_id,
            "genres": movie.genres,
            "profit_margin": profit_margin
        }
        
        movie_responses.append(MovieResponse(**movie_dict))
    
    return MovieListResponse(
        movies=movie_responses,
        total=total_count,
        page=page,
        per_page=limit,
        pages=total_pages
    )


@router.get("/movies/top/rated", response_model=List[MovieResponse])
async def get_top_rated_movies(
    limit: int = Query(10, ge=1, le=100, description="Number of top movies to return"),
    min_votes: int = Query(100, ge=1, description="Minimum number of votes required"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    year: Optional[int] = Query(None, ge=1900, le=2030, description="Filter by release year"),
    db: Session = Depends(get_db),
    api_key: APIKey = Security(validate_api_key)  # 🔑 API KEY REQUIRED (lightweight)
):
    """
    Get the highest rated movies with a minimum vote threshold.
    
    **Requires API key authentication.**
    
    This prevents movies with just a few perfect ratings from dominating the list.
    You can also filter the top rated movies by genre or year.
    
    Example: /movies/top/rated?limit=20&min_votes=500&genre=Animation&year=2020
    """
    
    # Start with base query
    query = db.query(Movie).filter(
        Movie.vote_count >= min_votes,
        Movie.vote_average.isnot(None)
    )
    
    # Apply optional filters
    if genre:
        query = query.filter(Movie.genres.like(f'%"name": "{genre}"%'))
    
    if year:
        query = query.filter(func.strftime('%Y', Movie.release_date) == str(year))
    
    # Order by vote_average (desc), then by vote_count (desc) as tiebreaker
    movies = (
        query
        .order_by(desc(Movie.vote_average), desc(Movie.vote_count))
        .limit(limit)
        .all()
    )
    
    # Transform with calculated fields
    movie_responses = []
    for movie in movies:
        profit_margin = None
        if movie.budget and movie.budget > 0 and movie.revenue and movie.revenue > 0:
            profit_margin = round(((movie.revenue - movie.budget) / movie.budget) * 100, 2)
        
        movie_dict = {
            "id": movie.id,
            "title": movie.title,
            "original_title": movie.original_title,
            "overview": movie.overview,
            "release_date": movie.release_date,
            "runtime": movie.runtime,
            "vote_average": movie.vote_average,
            "vote_count": movie.vote_count,
            "popularity": movie.popularity,
            "budget": movie.budget,
            "revenue": movie.revenue,
            "poster_path": movie.poster_path,
            "imdb_id": movie.imdb_id,
            "genres": movie.genres,
            "profit_margin": profit_margin
        }
        
        movie_responses.append(MovieResponse(**movie_dict))
    
    return movie_responses


@router.get("/movies/top/grossing", response_model=List[MovieResponse])
async def get_top_grossing_movies(
    limit: int = Query(10, ge=1, le=100, description="Number of top grossing movies to return"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    year_from: Optional[int] = Query(None, ge=1900, le=2030, description="Movies from this year onwards"),
    year_to: Optional[int] = Query(None, ge=1900, le=2030, description="Movies up to this year"),
    min_budget: Optional[int] = Query(None, ge=0, description="Minimum budget (to exclude low-budget successes)"),
    db: Session = Depends(get_db),
    api_key: APIKey = Security(validate_api_key)  # 🔑 API KEY REQUIRED
):
    """
    Get the highest grossing movies by box office revenue.
    
    **Requires API key authentication.**
    
    Features:
    - Filter by genre to see top grossers in specific categories
    - Filter by year range to compare different eras
    - Set minimum budget to focus on big-budget blockbusters
    - Shows profit margins for financial analysis
    
    Example: /movies/top/grossing?limit=20&genre=Action&year_from=2010&min_budget=100000000
    """
    
    # Start with movies that have revenue data
    query = db.query(Movie).filter(Movie.revenue > 0)
    
    # Apply optional filters
    if genre:
        query = query.filter(Movie.genres.like(f'%"name": "{genre}"%'))
    
    if year_from:
        query = query.filter(func.strftime('%Y', Movie.release_date) >= str(year_from))
    
    if year_to:
        query = query.filter(func.strftime('%Y', Movie.release_date) <= str(year_to))
    
    if min_budget:
        query = query.filter(Movie.budget >= min_budget)
    
    # Order by revenue (highest first)
    movies = (
        query
        .order_by(desc(Movie.revenue))
        .limit(limit)
        .all()
    )
    
    # Transform with calculated fields (profit margin is especially interesting here)
    movie_responses = []
    for movie in movies:
        profit_margin = None
        roi = None  # Return on Investment
        
        if movie.budget and movie.budget > 0 and movie.revenue and movie.revenue > 0:
            profit_margin = round(((movie.revenue - movie.budget) / movie.budget) * 100, 2)
            roi = round(movie.revenue / movie.budget, 2)
        
        movie_dict = {
            "id": movie.id,
            "title": movie.title,
            "original_title": movie.original_title,
            "overview": movie.overview,
            "release_date": movie.release_date,
            "runtime": movie.runtime,
            "vote_average": movie.vote_average,
            "vote_count": movie.vote_count,
            "popularity": movie.popularity,
            "budget": movie.budget,
            "revenue": movie.revenue,
            "poster_path": movie.poster_path,
            "imdb_id": movie.imdb_id,
            "genres": movie.genres,
            "profit_margin": profit_margin
        }
        
        movie_responses.append(MovieResponse(**movie_dict))
    
    return movie_responses


# Keep the stats endpoint public for now (no API key required)
@router.get("/movies/stats")
async def get_movie_stats(db: Session = Depends(get_db), api_key: APIKey = Security(validate_api_key)):
    """
    Get overview statistics about the movie database.
    
    **Public endpoint** - No API key required.
    
    Helpful for understanding your dataset and testing queries.
    """
    
    # Basic counts
    total_movies = db.query(Movie).count()
    movies_with_revenue = db.query(Movie).filter(Movie.revenue > 0).count()
    movies_with_budget = db.query(Movie).filter(Movie.budget > 0).count()
    
    # Rating statistics  
    rating_stats = db.query(
        func.avg(Movie.vote_average).label('avg_rating'),
        func.min(Movie.vote_average).label('min_rating'),
        func.max(Movie.vote_average).label('max_rating'),
        func.count(Movie.vote_average).label('rated_movies')
    ).filter(Movie.vote_average.isnot(None)).first()
    
    # Year range
    year_stats = db.query(
        func.min(func.strftime('%Y', Movie.release_date)).label('oldest_year'),
        func.max(func.strftime('%Y', Movie.release_date)).label('newest_year')
    ).filter(Movie.release_date.isnot(None)).first()
    
    # Financial stats (for movies with budget/revenue data)
    financial_stats = db.query(
        func.sum(Movie.revenue).label('total_revenue'),
        func.sum(Movie.budget).label('total_budget'),
        func.avg(Movie.revenue).label('avg_revenue'),
        func.avg(Movie.budget).label('avg_budget'),
        func.max(Movie.revenue).label('max_revenue'),
        func.max(Movie.budget).label('max_budget')
    ).filter(Movie.revenue > 0, Movie.budget > 0).first()
    
    return {
        "overview": {
            "total_movies": total_movies,
            "movies_with_revenue_data": movies_with_revenue,
            "movies_with_budget_data": movies_with_budget,
        },
        "ratings": {
            "average_rating": round(rating_stats.avg_rating, 2) if rating_stats.avg_rating else None,
            "min_rating": rating_stats.min_rating,
            "max_rating": rating_stats.max_rating,
            "movies_with_ratings": rating_stats.rated_movies
        },
        "timeline": {
            "oldest_movie_year": year_stats.oldest_year,
            "newest_movie_year": year_stats.newest_year
        },
        "financials": {
            "total_box_office": financial_stats.total_revenue if financial_stats else None,
            "total_budgets": financial_stats.total_budget if financial_stats else None,
            "average_revenue": round(financial_stats.avg_revenue, 2) if financial_stats and financial_stats.avg_revenue else None,
            "average_budget": round(financial_stats.avg_budget, 2) if financial_stats and financial_stats.avg_budget else None,
            "highest_grossing": financial_stats.max_revenue if financial_stats else None,
            "biggest_budget": financial_stats.max_budget if financial_stats else None
        },
        "note": "This endpoint is public. Other movie endpoints require API key authentication."
    }