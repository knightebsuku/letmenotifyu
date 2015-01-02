import sqlite3
import logging
import time
from notifylib import settings
from notifylib.movies import fetch_torrent
from notifylib.movies import (get_upcoming_movies, insert_upcoming_movies,
                              get_released_movies, insert_released_movies)


def process_movie_queue():
    while 1:
        connect = sqlite3.connect(settings.DATABASE_PATH)
        cursor = connect.cursor()
        connect.execute("PRAGMA journal_mode=WAL")
        check_upcoming_queue(connect, cursor)
        cursor.execute("SELECT title,mq.id,mtl.link,mtl.hash_sum,watch_queue_status_id FROM "+
                       "movie_torrent_links as mtl "+
                       " join movie_queue as mq "+
                       "on mtl.movie_id=mq.movie_id "+
                       "join movies on mtl.movie_id=movies.id ")
        new_queue = cursor.fetchall()
        for data in  new_queue:
            if data[4] == 1:
                logging.debug("new movie in queue, downloading torrent")
                if fetch_torrent(data[2], data[0], cursor, data[3]):
                    try:
                        connect.execute("UPDATE movie_queue set watch_queue_status_id=2 where id=?",
                                    (data[1],))
                        connect.commit()
                    except Exception:
                        logging.warn("unable to update movie_queue")
            else:
                logging.debug('no new queues')
        connect.execute("PRAGMA wal_checkpoint(PASSIVE)")
        connect.close()
        time.sleep(600)
        

def update():
    while 1:
        connect = sqlite3.connect(settings.DATABASE_PATH)
        cursor = connect.cursor()
        connect.execute("PRAGMA journal_mode=WAL")
        movie(connect, cursor)
        connect.close()
        time.sleep(600)

def movie(connect, cursor):
    upcoming_movie_data = get_upcoming_movies()
    insert_upcoming_movies(upcoming_movie_data, connect, cursor)
    released_movie_data = get_released_movies()
    insert_released_movies(released_movie_data, cursor, connect)

def check_upcoming_queue(connect,cursor):
    "move upcoming queue movie to movie_queue"
    cursor.execute("SELECT title FROM upcoming_queue")
    data = cursor.fetchall()
    for title in data:
        cursor.execute("SELECT id FROM movies WHERE title=?",(title[0],))
        if cursor.fetchone():
            try:
                cursor.execute("INSERT INTO movie_queue(movie_id,watch_queue_status_id) "+
                            "SELECT movies.id,watch_queue_status.id FROM movies,watch_queue_status "+
                            "WHERE movies.title=? AND watch_queue_status.name='new'",(title[0],))
                connect.execute("DELETE FROM upcoming_queue WHERE title=?",(title[0],))
                connect.commit()
                logging.debug("moved {} to movie_queue".format(title[0]))
            except sqlite3.IntegrityError:
                logging.info("record already exists in movie_queue")
                connect.execute("DELETE FROM upcoming_queue WHERE title=?",(title[0],))
            
