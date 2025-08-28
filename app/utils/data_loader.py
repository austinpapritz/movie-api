import pandas as pd
import json
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.movie import Movie
from ..database import engine, Base

def load_csv_data(csv_path: str):
    """Load movie data from CSV into database"""
    Base.metadata.create_all(bind=engine)
    
    df = pd.read_csv(csv_path)
    
    # Clean and process the data
    def safe_json_loads(x):
        if pd.isna(x) or x == '':
            return []
        try:
            return json.loads(x.replace("'", '"'))
        except:
            return []
    
    def safe_date_parse(date_str):
        if pd.isna(date_str):
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None
    
    # Process JSON columns
    json_columns = ['genres', 'production_companies', 'production_countries', 
                   'spoken_languages', 'belongs_to_collection']
    
    for col in json_columns:
        df[col] = df[col].apply(safe_json_loads)
    
    # Process other columns
    df['release_date'] = df['release_date'].apply(safe_date_parse)
    df['adult'] = df['adult'].map({'True': True, 'False': False})
    df['video'] = df['video'].map({'True': True, 'False': False})
    
    # Convert to Movie objects
    session = Session(engine)
    
    try:
        for _, row in df.iterrows():
            movie = Movie(
                id=row['id'],
                title=row['title'],
                original_title=row['original_title'],
                overview=row['overview'] if pd.notna(row['overview']) else None,
                tagline=row['tagline'] if pd.notna(row['tagline']) else None,
                release_date=row['release_date'],
                runtime=row['runtime'] if pd.notna(row['runtime']) else None,
                budget=row['budget'] if pd.notna(row['budget']) else 0,
                revenue=row['revenue'] if pd.notna(row['revenue']) else 0,
                vote_average=row['vote_average'] if pd.notna(row['vote_average']) else None,
                vote_count=row['vote_count'] if pd.notna(row['vote_count']) else 0,
                popularity=row['popularity'] if pd.notna(row['popularity']) else None,
                adult=row['adult'],
                video=row['video'],
                status=row['status'] if pd.notna(row['status']) else None,
                homepage=row['homepage'] if pd.notna(row['homepage']) else None,
                imdb_id=row['imdb_id'] if pd.notna(row['imdb_id']) else None,
                poster_path=row['poster_path'] if pd.notna(row['poster_path']) else None,
                original_language=row['original_language'] if pd.notna(row['original_language']) else None,
                genres=row['genres'],
                production_companies=row['production_companies'],
                production_countries=row['production_countries'],
                spoken_languages=row['spoken_languages'],
                belongs_to_collection=row['belongs_to_collection'] if row['belongs_to_collection'] else None
            )
            session.add(movie)
        
        session.commit()
        print(f"Successfully loaded {len(df)} movies into database")
    
    except Exception as e:
        session.rollback()
        print(f"Error loading data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    load_csv_data("../movie-archive/movies.csv")