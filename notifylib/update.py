#!/usr/bin/python

import time
import os
import sqlite3 as sqlite

from notifylib.series_update import get_series
from notifylib.movies_update import get_movies

#separate database instance
sqlite_file = os.environ['HOME']+'/.local/share/letmenotifyu/letmenotifyu.sqlite'

def update_databases():
    connection = sqlite.connect(sqlite_file)
    cursor = connection.cursor()
    try:
        get_series(cursor, connection)
        get_movies(cursor, connection)
        print "Updated"
        time.sleep(21600) #wait 6 hrs
    except Exception, e:
        print e
        time.sleep(300) #wait 5min
    finally:
        update_databases()

