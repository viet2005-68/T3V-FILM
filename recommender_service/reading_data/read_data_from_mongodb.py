from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from pathlib import Path
import asyncio

GENRES = ['action', 'adventure', 'comedy', 'crime', 'fantasy', 'historical',
         'horror', 'romance', 'sci-fi', 'thriller', 'western', 'animation',
         'drama', 'documentary']

def load_mongo_db():
    # Load environment variables from .env file
    env_path = Path(__file__).resolve().parents[1] / "env" / ".env"
    load_dotenv(dotenv_path=env_path)

    # MongoDB URI and DB Name from environment variables
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME")

    # Set up MongoDB connection
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    return db

async def get_all_movies():
    db = load_mongo_db()
    movies = await db.movies.find().to_list()
    return movies

async def get_all_users():
    db = load_mongo_db()
    # Define the aggregation pipeline for fetching users with favorite movies populated
    pipeline = [
        {
            "$lookup": {
                "from": "movies",  # Join with the 'movies' collection
                "localField": "favorites",  # Field in 'users' that contains movie IDs (foreign key)
                "foreignField": "_id",  # Field in 'movies' collection that is referenced (primary key)
                "as": "favorite_movies"  # New field that will contain the populated movie data
            }
        },
        {
            "$unwind": {
                "path": "$favorite_movies",  # Unwind the 'favorite_movies' array to flatten it
                "preserveNullAndEmptyArrays": True  # Keep users even if they have no favorites
            }
        },
        {
            "$group": {
                "_id": "$_id",  # Group by user ID
                "username": {"$first": "$username"},
                "email": {"$first": "$email"},
                "profilePic": {"$first": "$profilePic"},
                "age": {"$first": "$age"},
                "favoriteGenre": {"$first": "$favoriteGenre"},
                "gender": {"$first": "$gender"},
                "favorites": {"$push": "$favorite_movies"},  # Rebuild the favorites array with populated movie data
            }
        }
    ]

    # Execute the aggregation pipeline
    cursor = db.users.aggregate(pipeline)
    
    # Fetch all the aggregated results as a list
    users_with_favorites = await cursor.to_list(length=None)
    
    return users_with_favorites

# Function to get both movies and users in parallel
async def get_data():
    movies, users = await asyncio.gather(get_all_movies(), get_all_users())
    return movies, users

# Execute the function and print results
def fetch_data_final():
    movies, users = asyncio.run(get_data())
    return movies, users