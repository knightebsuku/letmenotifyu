#!/usr/bin/python3


import os

from libletmenotifyu import database as db
#from libletmenotifyu.main import Main
from libletmenotifyu import settings
from libletmenotifyu import util

#os.chdir(settings.DATA_FILES_PATH)

if __name__ == "__main__":
    util.start_logging()
    if not os.path.isdir(settings.DIRECTORY_PATH):
        os.mkdir(settings.DIRECTORY_PATH)
        settings.initial()
        db.create_db('movie.sqlite')
        db.create_db('series.db')
    else:
        db.migrate()
    #Main(series_process, movie_process, movie_details)    
