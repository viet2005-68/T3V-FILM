import os 
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
from training.preprocess import compute_user_vectors, compute_movie_vectors
import numpy as np
import tensorflow as tf
from pprint import pprint
from collections import OrderedDict
import pandas as pd
from itertools import islice

def preprocess():
    user_vec, user_dict = compute_user_vectors()
    movie_vec, movie_dict, _ = compute_movie_vectors()

    user_mean = np.load('data/params/user_mean.npy')
    user_std = np.load('data/params/user_std.npy')
    movie_mean = np.load('data/params/movie_mean.npy')
    movie_std = np.load('data/params/movie_std.npy')
    movie_std[movie_std <= 0.05] = 1

    user_vec_scale = (user_vec - user_mean) / (user_std + 1e-8)
    movie_vec_scale = (movie_vec - movie_mean) / (movie_std)
    return user_vec_scale, movie_vec_scale, user_dict, movie_dict

def get_alreay_rate(user_id):
    already_rate = set()
    df_user_movie = pd.read_csv(os.path.join(project_root, r"data\record\user_movie.csv"))
    for ind, row in df_user_movie.iterrows():
        if row["User Id"] == user_id:
            already_rate.add(row["Movie Id"])
    return already_rate
    

def inference(user_id, n=10):
    already_rate = get_alreay_rate(user_id)
    user_vec, movie_vec, user_dict, movie_dict = preprocess()
    movie_dict_rev = {v: k for k, v in movie_dict.items()}
    model = tf.keras.models.load_model('data\\model\\contentbased_filtering.keras')
    # Loop through all movies to get rating (for small dataset)
    user_movie_dict = {}
    for idx, movie in enumerate(movie_vec):
        if movie_dict_rev[idx] in already_rate:
            continue
        prediction_rating = model.predict([user_vec[user_dict[user_id]].reshape(-1, user_vec[user_dict[user_id]].shape[0]), movie.reshape(-1, movie.shape[0])], verbose=0)
        # Take only rating that is greater or equal to 3
        if prediction_rating[0][0] >= 3:
            user_movie_dict[movie_dict_rev[idx]] = prediction_rating[0][0]
    sorted_dict = OrderedDict(sorted(user_movie_dict.items(), key=lambda item: item[1], reverse=True))
    top_n = OrderedDict(islice(sorted_dict.items(), n))
    return top_n