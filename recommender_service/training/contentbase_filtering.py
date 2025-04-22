from preprocess import compute_training_vectors
import tensorflow as tf
import numpy as np
from sklearn.model_selection import train_test_split

user_train_vec, movie_train_vec, y_train_vec = compute_training_vectors()
num_outputs = 64
user_features = user_train_vec.shape[1]
movie_features = movie_train_vec.shape[1]

user_train, user_val, movie_train, movie_val, y_train, y_val = train_test_split(
    user_train_vec, movie_train_vec, y_train_vec, test_size=0.1, shuffle=True
)

def z_score_normalization(X):
    mui = np.mean(X, axis=0)
    std = np.std(X, axis=0)
    X_scale = (X - mui) / (std + 1e-8)
    return X_scale

user_train_scale = z_score_normalization(user_train)
movie_train_scale = z_score_normalization(movie_train)
user_val_scale = z_score_normalization(user_val)
movie_val_scale = z_score_normalization(movie_val)

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

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
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
print(model.predict([user_val_scale, movie_val_scale]).flatten())
print("-------------------ACTUALS----------------------------------")
print(y_val)
print("MSE: ", model.evaluate([user_val_scale, movie_val_scale], y_val))