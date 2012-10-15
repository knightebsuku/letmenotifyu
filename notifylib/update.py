#!/usr/bin/env python

from notifylib.series_update import get_series
from notifylib.movies_update import get_movies
import time,os

movie_path=os.environ['HOME']+'/.local/share/letmenotifyu/movies.sqlite'
series_path=os.environ['HOME']+'/.local/share/letmenotifyu/url.sqlite'
    
def update_databases():
        try:
            get_series(series_path)
            get_movies(movie_path)
            time.sleep(21600) #wait 6 hrs
            update_databases()
        except Exception, e:
            print e   
            time.sleep(300) #wait 5min
            update_databases()

