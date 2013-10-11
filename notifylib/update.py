
import time
import sqlite3 as sqlite

from notifylib.series_update import get_series
from notifylib.movies_update import get_movies


def update_movie_series(sqlite_file):
    connection = sqlite.connect(sqlite_file)
    cursor = connection.cursor()
    try:
        get_series(cursor, connection)
        print("PRINT")
        get_movies(cursor, connection)
        time.sleep(21600) #6hrs
    except Exception as e:
        print(e)
        print("Cant UPDATE")
        time.sleep(300) #wait 5min
    finally:
        connection.close()
        update_movie_series(sqlite_file)

