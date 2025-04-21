from read_data_from_mongodb import fetch_data_final, GENRES
from user_feature import User
from movie_feature import Movie

movies, users = fetch_data_final()

# User features dictionary
user_features_map = {}

# Movie features dictionary
movie_features_map = {}

# User-Movie rating
user_movie_rating = {}

# Compute user features
for user in users:
    newUser = User(age=user.get('age'), gender=user.get('gender'), favorite_genre=user.get("favoriteGenre"))
    newUser.compute_favorite_per_genre_feature(user.get('favorites'))
    user_features_map[user.get('_id')] = newUser

for movie in movies:
    for review in movie['reviews']:
        user_id = review['user']
        rating = review['rating']
        currentRatingCount = getattr(user_features_map[user_id], f"{movie['genre']}RatingCount")
        setattr(user_features_map[user_id], f"{movie['genre']}RatingCount", currentRatingCount + 1)
        currentRatingTotal = getattr(user_features_map[user_id], f"{movie['genre']}RatingTotal")
        setattr(user_features_map[user_id], f"{movie['genre']}RatingTotal", currentRatingTotal + rating)

# Compute movie features
for movie in movies:
    newMovie = Movie(genre=movie.get('genre'), year=movie.get('year'), limit=movie.get('limit'), is_series=movie.get('isSeries'), title=movie.get('title'))
    newMovie.compute_avg_rating(movie.get('reviews'))
    movie_features_map[movie.get('_id')] = newMovie

# Compute user-movie rating dict
for movie in movies:
    for review in movie.get('reviews'):
        user_movie_rating[(review.get('user'), movie.get('_id'))] = review.get('rating')