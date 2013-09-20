#!/usr/bin/python3

import time
import sqlite3 as sqlite

from notifylib.series_update import get_series
from notifylib.movies_update import get_movies


def update_movie_series(db_file):
    connection = sqlite.connect(db_file)
    cursor = connection.cursor()
    try:
        get_series(db_file)
        get_movies(db_file)
        time.sleep(21600)
    except Exception as e:
        print(e)
        time.sleep(300)
    finally:
        update_movie_series(db_file)

