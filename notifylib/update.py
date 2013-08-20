#!/usr/bin/python3

import time
import sqlite3 as sqlite

from notifylib.series_update import get_series
from notifylib.movies_update import get_movies


def update_movie_series(sqlite_file):
    connection = sqlite.connect(sqlite_file)
    cursor = connection.cursor()
    try:
        #get_series(cursor, connection)
        get_movies(cursor, connection)
        #Will add log function with time stamp to add to log file
        print("Updated")
        time.sleep(21600) #wait 6 hrs
    except Exception as e:
        #Add log fuction to log output
        print(e)
        time.sleep(300) #wait 5min
    finally:
        update_movie_series(sqlite_file)

