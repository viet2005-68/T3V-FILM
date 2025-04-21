import os 
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
import pandas as pd
import numpy as np
from reading_data.read_data_from_mongodb import GENRES

# Computing movie vector
def compute_movie_vectors():
    '''
    Returns:
        movie_vec: Vector representation of numeric movie features
        movie_title: Movie's Title
    '''
    movie_id_dict = {}
    df_movie = pd.read_csv(os.path.join(project_root, r'data\movie.csv'))
    for genre in GENRES:
        df_movie[f"Genre {genre}"] = df_movie['Genre'].apply(lambda x: 1 if x == genre else 0)
    df_numeric = df_movie.drop(columns=['Id', 'Title', 'Genre'])
    movie_vec = df_numeric.to_numpy()
    for ind, row in enumerate(df_movie["Id"]):
        movie_id_dict[row] = ind
    return movie_vec, movie_id_dict, df_movie["Title"].to_numpy()

# Computing user's vector
def compute_user_vectors():
    '''
    Returns
    '''
    user_id_dict = {}
    df_user = pd.read_csv(os.path.join(project_root, r"data\user.csv"))
    df_user = df_user.fillna(0)
    for genre in GENRES:
        df_user[f"Favorite {genre}"] = df_user['Favorite genre'].apply(lambda x: 1 if x == genre else 0)
    df_user["Gender"] = df_user["Gender"].apply(lambda x: 1 if x == 'male' else 0) 
    df_numeric = df_user.drop(columns=["Id", 'Favorite genre'])
    user_vec = df_numeric.to_numpy()
    for ind, row in enumerate(df_user["Id"]):
        user_id_dict[row] = ind
    return user_vec, user_id_dict

def compute_training_vectors():
    movie_vec, movie_id_dict, movie_title = compute_movie_vectors()
    user_vec, user_id_dict = compute_user_vectors()
    df_user_movie = pd.read_csv(os.path.join(project_root, r"data\user_movie.csv"))
    movie_train_vec = np.zeros(shape=(len(df_user_movie), movie_vec.shape[1]))
    user_train_vec = np.zeros(shape=(len(df_user_movie), user_vec.shape[1]))
    y_train = np.zeros(shape=(len(df_user_movie)))
    for ind, row in df_user_movie.iterrows():
        user_id = row["User Id"]
        movie_id = row["Movie Id"]
        rating = row["Rating"]
        movie_train_vec[ind] = movie_vec[movie_id_dict[movie_id]]
        user_train_vec[ind] = user_vec[user_id_dict[user_id]]
        y_train[ind] = rating
    return user_train_vec, movie_train_vec, y_train