#!/usr/bin/python3


import os

from watchme import database as db
#from watchme.main import Main
from watchme import settings
from watchme import util
from watchme import movie
from watchme import movie_detail
import time

#os.chdir(settings.DATA_FILES_PATH)

if __name__ == "__main__":
    if not os.path.isdir(settings.DIRECTORY_PATH):
        os.mkdir(settings.DIRECTORY_PATH)
        util.start_logging()
        settings.initial()
        db.create_db(settings.MOVIE_DB_PATH)
        db.create_db(settings.SERIES_DB_PATH)
        db.migrate()
    else:
        util.start_logging()
        db.migrate()
    movie.new_movies()
    #movie_detail.fetch_movie_detail()
    
    #Main(series_process, movie_process, movie_details)    
