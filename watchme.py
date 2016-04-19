#!/usr/bin/python3


import os

from libletmenotifyu import database as db
#from libletmenotifyu.main import Main
from libletmenotifyu import settings
from libletmenotifyu import util
from libletmenotifyu import movie
from libletmenotifyu import movie_detail
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
    #movie.get_new_movies()
    movie_detail.fetch_movie_detail()
    
    #Main(series_process, movie_process, movie_details)    
