#!/usr/bin/python3


import os

from libletmenotifyu import database as db
#from libletmenotifyu.main import Main
from libletmenotifyu import settings
from libletmenotifyu import util
from libletmenotifyu import movie
from libletmenotifyu import movie_detail

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
    #movie.movie_page()
    movie_detail.get_detail('https://kat.cr/home-invasion-2016-dvdrip-xvid-etrg-t12003832.html')
    #Main(series_process, movie_process, movie_details)    
