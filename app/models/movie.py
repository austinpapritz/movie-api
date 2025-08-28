from sqlalchemy import Column, Integer, String, Float, Date, Boolean, Text, JSON
from ..database import Base

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    original_title = Column(String)
    overview = Column(Text)
    tagline = Column(String)
    release_date = Column(Date)
    runtime = Column(Float)
    budget = Column(Integer)
    revenue = Column(Integer)
    vote_average = Column(Float)
    vote_count = Column(Integer)
    popularity = Column(Float)
    adult = Column(Boolean, default=False)
    video = Column(Boolean, default=False)
    status = Column(String)
    homepage = Column(String)
    imdb_id = Column(String, index=True)
    poster_path = Column(String)
    original_language = Column(String)
    
    # JSON fields
    genres = Column(JSON)
    production_companies = Column(JSON)
    production_countries = Column(JSON)
    spoken_languages = Column(JSON)
    belongs_to_collection = Column(JSON)