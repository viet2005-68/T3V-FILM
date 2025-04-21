from read_data_from_mongodb import GENRES
from pprint import pprint

class User:
    def __init__(self, age, gender, favorite_genre):
        self.age = age
        self.gender = gender
        self.favorite_genre = favorite_genre
        for genre in GENRES:
            setattr(self, f"{genre}FavoriteCount", 0)
            setattr(self, f"{genre}RatingTotal", 0)
            setattr(self, f"{genre}RatingCount", 0)
    
    def get_info(self):
        pprint(self.__dict__)
    
    def compute_favorite_per_genre_feature(self, favorites):
        for favorite in favorites:
            genre = favorite["genre"]
            current_value = getattr(self, f"{genre}FavoriteCount", 0)
            setattr(self, f"{genre}FavoriteCount", current_value + 1)