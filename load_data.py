import pandas as pd
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.movie import Movie
from app.database import engine, Base

def safe_float_convert(value):
    """Safely convert value to float, return None if not possible"""
    if pd.isna(value) or value == '' or value is None:
        return None
    if isinstance(value, str):
        # Remove any non-numeric characters and try again
        cleaned = ''.join(c for c in value if c.isdigit() or c in '.-')
        if not cleaned or cleaned in ['.', '-', '.-']:
            return None
        try:
            return float(cleaned)
        except:
            return None
    try:
        return float(value)
    except:
        return None

def safe_int_convert(value):
    """Safely convert value to int, return 0 if not possible"""
    if pd.isna(value) or value == '' or value is None:
        return 0
    if isinstance(value, str):
        cleaned = ''.join(c for c in value if c.isdigit())
        if not cleaned:
            return 0
        try:
            return int(cleaned)
        except:
            return 0
    try:
        return int(value)
    except:
        return 0

def load_csv_data():
    """Load movie data from CSV into database with robust error handling"""
    Base.metadata.create_all(bind=engine)
    
    csv_path = "movie-archive/movies.csv"
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Found {len(df)} movies in CSV")
    
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
            return datetime.strptime(str(date_str), '%Y-%m-%d').date()
        except:
            return None
    
    # Process JSON columns
    json_columns = ['genres', 'production_companies', 'production_countries', 
                   'spoken_languages', 'belongs_to_collection']
    
    for col in json_columns:
        if col in df.columns:
            df[col] = df[col].apply(safe_json_loads)
    
    # Clean numeric columns that might have text
    print("Cleaning numeric columns...")
    df['budget'] = df['budget'].apply(safe_int_convert)
    df['revenue'] = df['revenue'].apply(safe_float_convert).fillna(0)
    df['vote_average'] = df['vote_average'].apply(safe_float_convert)
    df['vote_count'] = df['vote_count'].apply(safe_int_convert)
    df['popularity'] = df['popularity'].apply(safe_float_convert)
    df['runtime'] = df['runtime'].apply(safe_float_convert)
    
    # Process other columns
    df['release_date'] = df['release_date'].apply(safe_date_parse)
    df['adult'] = df['adult'].map({'True': True, 'False': False, True: True, False: False, 'true': True, 'false': False}).fillna(False)
    df['video'] = df['video'].map({'True': True, 'False': False, True: True, False: False, 'true': True, 'false': False}).fillna(False)
    
    # Load into database in batches
    session = Session(engine)
    batch_size = 1000
    
    try:
        loaded_count = 0
        failed_count = 0
        
        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i + batch_size]
            batch_movies = []
            
            for _, row in batch_df.iterrows():
                try:
                    movie = Movie(
                        id=row['id'],
                        title=str(row['title']) if pd.notna(row['title']) else "Unknown Title",
                        original_title=str(row['original_title']) if pd.notna(row['original_title']) else None,
                        overview=str(row['overview']) if pd.notna(row['overview']) else None,
                        tagline=str(row['tagline']) if pd.notna(row['tagline']) else None,
                        release_date=row['release_date'],
                        runtime=row['runtime'],
                        budget=row['budget'],
                        revenue=row['revenue'],
                        vote_average=row['vote_average'],
                        vote_count=row['vote_count'],
                        popularity=row['popularity'],
                        adult=bool(row['adult']),
                        video=bool(row['video']),
                        status=str(row['status']) if pd.notna(row['status']) else None,
                        homepage=str(row['homepage']) if pd.notna(row['homepage']) else None,
                        imdb_id=str(row['imdb_id']) if pd.notna(row['imdb_id']) else None,
                        poster_path=str(row['poster_path']) if pd.notna(row['poster_path']) else None,
                        original_language=str(row['original_language']) if pd.notna(row['original_language']) else None,
                        genres=row['genres'] if 'genres' in row else [],
                        production_companies=row['production_companies'] if 'production_companies' in row else [],
                        production_countries=row['production_countries'] if 'production_countries' in row else [],
                        spoken_languages=row['spoken_languages'] if 'spoken_languages' in row else [],
                        belongs_to_collection=row['belongs_to_collection'] if pd.notna(row['belongs_to_collection']) and row['belongs_to_collection'] else None
                    )
                    batch_movies.append(movie)
                    
                except Exception as e:
                    failed_count += 1
                    print(f"Failed to process movie ID {row.get('id', 'unknown')}: {e}")
                    continue
            
            # Add batch to session
            session.add_all(batch_movies)
            session.commit()
            
            loaded_count += len(batch_movies)
            print(f"Loaded batch {i//batch_size + 1}: {loaded_count} movies total, {failed_count} failed")
        
        print(f"✅ Successfully loaded {loaded_count} movies into database")
        if failed_count > 0:
            print(f"⚠️  {failed_count} movies failed to load due to data issues")
    
    except Exception as e:
        session.rollback()
        print(f"❌ Error loading data: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    load_csv_data()