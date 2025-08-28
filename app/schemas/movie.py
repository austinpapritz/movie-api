from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date

class GenreSchema(BaseModel):
    id: int
    name: str

class ProductionCompanySchema(BaseModel):
    id: int
    name: str

class MovieBase(BaseModel):
    title: str
    overview: Optional[str] = None
    release_date: Optional[date] = None
    runtime: Optional[float] = None
    vote_average: Optional[float] = None
    genres: Optional[List[Dict[str, Any]]] = []

class MovieCreate(MovieBase):
    pass

class MovieResponse(MovieBase):
    id: int
    budget: Optional[int] = None
    revenue: Optional[int] = None
    vote_count: Optional[int] = None
    popularity: Optional[float] = None
    poster_path: Optional[str] = None
    imdb_id: Optional[str] = None
    profit_margin: Optional[float] = None  # Calculated field
    
    class Config:
        from_attributes = True

class MovieListResponse(BaseModel):
    movies: List[MovieResponse]
    total: int
    page: int
    per_page: int
    pages: int

class MovieFilters(BaseModel):
    genre: Optional[str] = None
    min_rating: Optional[float] = Field(None, ge=0, le=10)
    max_rating: Optional[float] = Field(None, ge=0, le=10)
    year: Optional[int] = None
    min_budget: Optional[int] = None
    language: Optional[str] = None
    sort_by: Optional[str] = Field("popularity", regex="^(popularity|vote_average|release_date|revenue|budget)$")
    order: Optional[str] = Field("desc", regex="^(asc|desc)$")