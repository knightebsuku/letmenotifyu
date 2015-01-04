#!/usr/bin/python3

import sqlite3
import logging
import time
import gzip
from notifylib import settings
from notifylib.movies import (get_upcoming_movies, insert_upcoming_movies,
                              get_released_movies, insert_released_movies)
from notifylib.series import Series
from notifylib import util
from notifylib import kickass
from urllib.request import urlopen
import os

def update():
    "update movies and series"
    while 1:
        connect = sqlite3.connect(settings.DATABASE_PATH)
        cursor = connect.cursor()
        connect.execute("PRAGMA journal_mode=WAL")
        movie(connect, cursor)
        series(connect, cursor)
        connect.close()
        #interval = get_process_interval(cursor)
        time.sleep(6000)

def process_series_queue():
    "handle the series queues"
    connect = sqlite3.connect(settings.DATABASE_PATH)
    cursor = connect.cursor()
    connect.execute("PRAGMA journal_mode=WAL")
    while 1:
        logging.debug("processing series queues")
        api_file = fetch_kickass_file()
        cursor.execute("SELECT title, series_queue.id, episode_name,watch_queue_status_id "+
                       'FROM  series_queue join series on series_id=series.id')
        queues = cursor.fetchall()
        for series_info in queues:
            if series_info[3] == 1:
                logging.debug("fetching episode torrent for {}".format(series_info[0]))
                episode_data = kickass.search_episode(api_file, series_info[0], series_info[2], "ettv")
                logging.debug(episode_data)
                if episode_data:
                    if util.fetch_torrent(episode_data[4].replace("\n",""),episode_data[1]):
                        try:
                            connect.execute("INSERT INTO series_torrent_links(series_queue_id,link) VALUES(?,?)",
                                (series_info[1],episode_data[4],))
                            connect.execute("UPDATE series_queue set watch_queue_status_id=2 where id=?",
                                    (series_info[1],))
                            connect.commit()
                        except sqlite3.IntegrityError:
                            logging.warn("link already exists in series_torrent_link table")
            elif series_info[3] == 2:
                logging.debug("Status 2 means that file has been downloaded waiting for transmission")
        time.sleep(6000)

def process_movie_queue():
    "handle movie queues"
    connect = sqlite3.connect(settings.DATABASE_PATH)
    cursor = connect.cursor()
    connect.execute("PRAGMA journal_mode=WAL")
    while 1:
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
                if util.fetch_torrent(data[2], data[0]):
                    try:
                        connect.execute("UPDATE movie_queue set watch_queue_status_id=2 where id=?",
                            (data[1],))
                        connect.commit()
                    except Exception:
                        logging.warn("unable to update movie_queue")
            else:
                logging.debug('no new queues')
        time.sleep(6000)
        

def movie(connect, cursor):
    upcoming_movie_data = get_upcoming_movies()
    insert_upcoming_movies(upcoming_movie_data, connect, cursor)
    released_movie_data = get_released_movies()
    insert_released_movies(released_movie_data, cursor, connect)

def series(connect,cursor):
    series_update = Series(connect,cursor)
    series_update.update_series()

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
            
def get_update_interval(cursor):
    cursor.execute("SELECT value FROM config WHERE key = 'update_interval'")
    update_interval = cursor.fetchone()
    return update_interval[0]
    
def get_process_interval(cursor):
    cursor.execute("SELECT value FROM config WHERE key='process_interval")
    process_interval = cursor.fetchone()
    return process_interval[0]


def fetch_kickass_file():
    kickass_file = urlopen("https://kickass.so/hourlydump.txt.gz")
    with gzip.open(kickass_file,'r') as gzip_file:
        with open(settings.KICKASS_FILE,'wb') as dump_file:
            for line in gzip_file:
                dump_file.write(line)
    logging.debug(settings.KICKASS_FILE)
    return settings.KICKASS_FILE
