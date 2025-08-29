# simple_loader.py
import pandas as pd
import json
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.movie import Movie
from app.database import engine, Base

def load_csv_data():
    """Load movie data from CSV - handle duplicates by dropping table first"""
    
    # Drop and recreate the table completely
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS movies"))
        conn.commit()
    
    Base.metadata.create_all(bind=engine)
    print("Created fresh movies table")
    
    csv_path = "movie-archive/movies.csv"
    print(f"Loading data from {csv_path}...")
    
    # Read CSV and remove duplicates by ID
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"Found {len(df)} total rows")
    
    # Remove duplicate IDs, keep first occurrence
    df = df.drop_duplicates(subset=['id'], keep='first')
    print(f"After removing duplicates: {len(df)} unique movies")
    
    # Simple cleaning
    df['budget'] = pd.to_numeric(df['budget'], errors='coerce').fillna(0).astype(int)
    df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce').fillna(0)
    df['runtime'] = pd.to_numeric(df['runtime'], errors='coerce')
    df['vote_average'] = pd.to_numeric(df['vote_average'], errors='coerce')
    df['vote_count'] = pd.to_numeric(df['vote_count'], errors='coerce').fillna(0).astype(int)
    df['popularity'] = pd.to_numeric(df['popularity'], errors='coerce')
    
    # Convert JSON-like strings to actual JSON strings (fix the single quotes)
    json_columns = ['genres', 'production_companies', 'production_countries', 
                   'spoken_languages', 'belongs_to_collection']
    
    for col in json_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).replace('nan', 'null')
    
    session = Session(engine)
    
    try:
        movies_added = 0
        for _, row in df.iterrows():
            try:
                # Parse date
                release_date = None
                if pd.notna(row['release_date']):
                    try:
                        release_date = datetime.strptime(str(row['release_date']), '%Y-%m-%d').date()
                    except:
                        pass
                
                movie = Movie(
                    id=int(row['id']),
                    title=str(row['title']) if pd.notna(row['title']) else "Unknown",
                    original_title=str(row['original_title']) if pd.notna(row['original_title']) else None,
                    overview=str(row['overview']) if pd.notna(row['overview']) else None,
                    tagline=str(row['tagline']) if pd.notna(row['tagline']) else None,
                    release_date=release_date,
                    runtime=row['runtime'] if pd.notna(row['runtime']) else None,
                    budget=int(row['budget']),
                    revenue=float(row['revenue']),
                    vote_average=row['vote_average'] if pd.notna(row['vote_average']) else None,
                    vote_count=int(row['vote_count']),
                    popularity=row['popularity'] if pd.notna(row['popularity']) else None,
                    adult=str(row.get('adult', 'False')).lower() == 'true',
                    video=str(row.get('video', 'False')).lower() == 'true',
                    status=str(row['status']) if pd.notna(row['status']) else None,
                    homepage=str(row['homepage']) if pd.notna(row['homepage']) else None,
                    imdb_id=str(row['imdb_id']) if pd.notna(row['imdb_id']) else None,
                    poster_path=str(row['poster_path']) if pd.notna(row['poster_path']) else None,
                    original_language=str(row['original_language']) if pd.notna(row['original_language']) else 'en',
                    # Store JSON columns as strings for now - we'll parse them properly later
                    genres=None,
                    production_companies=None,
                    production_countries=None,
                    spoken_languages=None,
                    belongs_to_collection=None
                )
                
                session.add(movie)
                movies_added += 1
                
                if movies_added % 1000 == 0:
                    session.commit()
                    print(f"Loaded {movies_added} movies...")
                    
            except Exception as e:
                print(f"Skipped movie ID {row.get('id', 'unknown')}: {e}")
                continue
        
        session.commit()
        print(f"Successfully loaded {movies_added} movies!")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    load_csv_data()