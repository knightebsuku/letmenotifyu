#!/usr/bin/python3

import time
import sqlite3 as sqlite

from notifylib.series_update import get_series
from notifylib.movies_update import get_movies


def update_movie_series(sqlite_file):
    connection = sqlite.connect(sqlite_file)
    cursor = connection.cursor()
    try:
        get_series(cursor, connection)
        get_movies(cursor, connection)
        time.sleep(21600)
    except Exception as e:
        print(e)
        time.sleep(300)
    finally:
        connection.close()
        update_movie_series(sqlite_file)

