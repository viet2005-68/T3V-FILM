from feature_extraction import user_movie_rating, user_features_map, movie_features_map
from read_data_from_mongodb import GENRES
import pandas as pd
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Write movie features data to csv file
movie_columns = ['Id', 'Title', 'Year', 'Limit', 'Genre', 'Avg rating', 'Total ratings']
df_movie = pd.DataFrame(columns = movie_columns)

for key, value in movie_features_map.items():
    new_row = pd.DataFrame([{
        'Id': key,
        'Title': value.title,
        'Year': value.year,
        'Limit': value.limit,
        'Genre': value.genre,
        'Avg rating': value.avg_rating,
        "Total ratings": value.number_of_ratings
    }])
    df_movie = pd.concat([df_movie, new_row], ignore_index=True)

df_movie.to_csv(os.path.join(project_root, r'data\movie.csv'), index=False)

# Write user features data to csv file
user_columns = ['Id', 'Age', 'Gender', 'Favorite genre']
for genre in GENRES:
    user_columns.append(f"{genre} favorite movies")
for genre in GENRES:
    user_columns.append(f"{genre} avg rating")
for genre in GENRES:
    user_columns.append(f"{genre} rating count")

df_user = pd.DataFrame(columns=user_columns)

for key, value in user_features_map.items():
    row_data = {
        'Id': key,
        'Age': value.age,
        'Gender': value.gender,
        'Favorite genre': value.favorite_genre
    }
    for genre in GENRES:
        total_rating_count = getattr(value, f"{genre}RatingCount", 0)
        total_rating_value = getattr(value, f"{genre}RatingTotal", 0)
        total_favorite = getattr(value, f"{genre}FavoriteCount", 0)
        row_data[f"{genre} favorite movies"] = total_favorite
        row_data[f"{genre} rating count"] = total_rating_count
        row_data[f"{genre} avg rating"] = total_rating_value / (total_rating_count if total_rating_count != 0 else 1)
    new_row_df = pd.DataFrame([row_data])
    df_user = pd.concat([df_user, new_row_df], ignore_index=True)

df_user.to_csv(os.path.join(project_root, r'data\user.csv'), index=False)


# Write user-movie rating to csv
user_movie_rating_columns = ['User Id', 'Movie Id', 'Rating']
df_user_movie_rating = pd.DataFrame(columns=user_movie_rating_columns)

for key, value in user_movie_rating.items():
    new_row_df = pd.DataFrame([{
        'User Id': key[0],
        'Movie Id': key[1],
        'Rating': value
    }])
    df_user_movie_rating = pd.concat([df_user_movie_rating, new_row_df], ignore_index=True)

df_user_movie_rating.to_csv(os.path.join(project_root, r'data\user_movie.csv'), index=False)
