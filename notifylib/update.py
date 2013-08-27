
import time
import sqlite3 as sqlite

from notifylib.series_update import get_series
from notifylib.movies_update import get_movies


def update_movie_series(sqlite_file):
    connection = sqlite.connect(sqlite_file)
    cursor = connection.cursor()
    try:
        get_series(cursor, connection)
        print("Series Updated")
        get_movies(cursor, connection)
        print("Movies Updated")
        connection.close()
        time.sleep(21600) #wait 6 hrs
    except Exception as e:
        print(e)
        connection.close()
        time.sleep(300) #wait 5min
    finally:
        update_movie_series(sqlite_file)

