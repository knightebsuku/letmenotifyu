
import time
import sqlite3

from notifylib.series_update import get_series
from notifylib.movies_update import get_movies


def update_movie_series(db_file):
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    try:
        get_series(cursor, connection)
        get_movies(cursor, connection)
        time.sleep(21600) #6hrs
    except Exception as e:
        print(e)
        time.sleep(300) #wait 5min
    finally:
        connection.close()
        update_movie_series(db_file)
