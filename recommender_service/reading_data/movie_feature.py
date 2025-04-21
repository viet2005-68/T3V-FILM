from read_data_from_mongodb import GENRES
from pprint import pprint

class Movie:
    def __init__(self, year, limit, genre, is_series, title):
        self.year = year
        self.limit = limit
        self.genre = genre
        self.avg_rating = 0
        self.number_of_ratings = 0
        self.is_series = is_series
        self.title = title
    
    def compute_avg_rating(self, reviews):
        for review in reviews:
            self.avg_rating += review['rating']
            self.number_of_ratings += 1
        self.avg_rating = self.avg_rating / self.number_of_ratings if self.number_of_ratings != 0 else 0

    def get_info(self):
        pprint(self.__dict__)