from preprocess import compute_training_vectors
import tensorflow as tf
import numpy as np
from sklearn.model_selection import train_test_split
from reading_data.convert_to_csv import populate_all
import os

populate_all()

user_train_vec, movie_train_vec, y_train_vec = compute_training_vectors()
num_outputs = 64
user_features = user_train_vec.shape[1]
movie_features = movie_train_vec.shape[1]

user_train, user_val, movie_train, movie_val, y_train, y_val = train_test_split(
    user_train_vec, movie_train_vec, y_train_vec, test_size=0.1, shuffle=True
)

def compute_scaling_params(X, type):
    mui = np.mean(X, axis=0)
    std = np.std(X, axis=0)
    np.save(f'data/params/{type}_mean.npy', mui)
    np.save(f'data/params/{type}_std.npy', std)
    return mui, std

def z_score_normalization(X, mui, std):
    return (X - mui) / (std)

user_mui, user_std = compute_scaling_params(user_train, "user")
movie_mui, movie_std = compute_scaling_params(movie_train, "movie")
# Avoid division by small number
movie_std[movie_std <= 0.05] = 1
user_std[user_std <= 0.05] = 1

user_train_scale = z_score_normalization(user_train, user_mui, user_std)
movie_train_scale = z_score_normalization(movie_train, movie_mui, movie_std)
user_val_scale = z_score_normalization(user_val, user_mui, user_std)
movie_val_scale = z_score_normalization(movie_val, movie_mui, movie_std)

def dnn_model():
    user_model = tf.keras.models.Sequential([
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(64),
    ])

    movie_model = tf.keras.models.Sequential([
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(64)
    ])

    input_user = tf.keras.layers.Input(shape=(user_features,))
    vu = user_model(input_user)

    input_movie = tf.keras.layers.Input(shape=(movie_features,))
    vm = movie_model(input_movie)

    concat = tf.keras.layers.Concatenate(axis=1)([vu, vm])

    concat_model = tf.keras.models.Sequential([
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(1)
    ])

    output = concat_model(concat)
    # output = tf.keras.layers.Dot(axes=1)([vu, vm])

    model = tf.keras.Model([input_user, input_movie], output)
    return model

model = dnn_model()
model.summary()

lr_schedule = tf.keras.optimizers.schedules.ExponentialDecay(
    initial_learning_rate=0.001,
    decay_steps=100,
    decay_rate=0.96,
    staircase=True
)

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=lr_schedule),
    loss=tf.keras.losses.MeanSquaredError()
)

model.fit([user_train_scale, movie_train_scale], y_train, validation_data=([user_val_scale, movie_val_scale], y_val), epochs=50)
print("-------------------TRAINING SETS--------------------------")
print("-------------------PREDICTIONS----------------------------")
print(model.predict([user_train_scale, movie_train_scale]).flatten())
print("-------------------ACTUALS--------------------------------")
print(y_train)
print("MSE: ", model.evaluate([user_train_scale, movie_train_scale], y_train))
print()
print("-------------------VALIDATION SETS--------------------------")
print("-------------------PREDICTIONS------------------------------")
print(model.predict([user_val_scale, movie_val_scale], verbose=0).flatten())
print("-------------------ACTUALS----------------------------------")
print(y_val)
print("MSE: ", model.evaluate([user_val_scale, movie_val_scale], y_val))

# Save model
save_dir = "data/model"
os.makedirs(save_dir, exist_ok=True)
model.save(os.path.join(save_dir, "contentbased_filtering.keras"))