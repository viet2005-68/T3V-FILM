from user_feature import User
from movie_feature import Movie

# Compute user features
def compute_user_features(users, movies):
    # User features dictionary
    user_features_map = {}
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
    return user_features_map



# Compute movie features
def compute_movie_features(movies):
    # Movie features dictionary
    movie_features_map = {}
    for movie in movies:
        newMovie = Movie(genre=movie.get('genre'), year=movie.get('year'), limit=movie.get('limit'), is_series=movie.get('isSeries'), title=movie.get('title'))
        newMovie.compute_avg_rating(movie.get('reviews'))
        movie_features_map[movie.get('_id')] = newMovie
    return movie_features_map

# Compute user-movie rating dict
def compute_user_movie_rating(movies):
    # User-Movie rating
    user_movie_rating = {}
    for movie in movies:
        for review in movie.get('reviews'):
            user_movie_rating[(review.get('user'), movie.get('_id'))] = review.get('rating')
    return user_movie_rating