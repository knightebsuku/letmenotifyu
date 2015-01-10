#!/usr/bin/python3

import sqlite3
import logging
import time
import gzip
import os

from letmenotifyu.notify import announce
from letmenotifyu import settings
from letmenotifyu.movies import (get_upcoming_movies, insert_upcoming_movies,
                              get_released_movies, insert_released_movies)
from letmenotifyu.series import Series
from letmenotifyu import util
from letmenotifyu import kickass
from threading import Thread
from urllib.request import urlopen


def start_threads():
    movie_process = Thread(target=process_movie_queue)
    movie_process.setDaemon(True)
    series_process = Thread(target=process_series_queue)
    series_process.setDaemon(True)
    all_update = Thread(target=update)
    all_update.setDaemon(True)
    movie_process.start()
    series_process.start()
    all_update.start()

def update():
    "update movies and series"
    while 1:
        connect = sqlite3.connect(settings.DATABASE_PATH)
        cursor = connect.cursor()
        connect.execute("PRAGMA journal_mode=WAL")
        movie(connect, cursor)
        series(connect, cursor)
        value = util.get_config_value(cursor,'update_interval')
        connect.close()
        time.sleep(int(value))

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
        for (title, queue_id, ep_name, watch_id) in queues:
            if watch_id == 1:
                logging.debug("fetching episode torrent for {}".format(title))
                try:
                    (_, series_title, _, _, episode_link) = kickass.search_episode(api_file, title, ep_name, "HDTV x264-LOL")
                    if util.fetch_torrent(episode_link.replace("\n",""),series_title):
                        try:
                            connect.execute("INSERT INTO series_torrent_links(series_queue_id,link) VALUES(?,?)",
                                (queue_id, episode_link,))
                            connect.execute("UPDATE series_queue set watch_queue_status_id=2 where id=?",
                                    (queue_id,))
                            connect.commit()
                        except sqlite3.IntegrityError:
                            logging.warn("link already exists in series_torrent_link table")
                except TypeError:
                    pass
            elif watch_id == 2:
                series_title = title.replace(" ",".")
                for dirs in os.listdir(settings.INCOMPLETE_DIRECTORY):
                    if dirs.startswith(series_title):
                        try:
                            connect.execute("UPDATE series_queue SET watch_queue_status_id=3 WHERE id=?",
                                        (queue_id,))
                            connect.commit()
                            break
                        except sqlite3.OperationalError as e:
                            logging.exception(e)
                            break
            elif watch_id == 3:
                series_title = title.replace(" ",".")
                for dirs in os.listdir(settings.COMPLETE_DIRECTORY):
                    if dirs.startswith(series_title):
                        try:
                            connect.execute("UPDATE series_queue set watch_queue_status_id=4 where id=?",
                                            (queue_id,))
                            connect.commit()
                            announce("Torrent Downloaded", "Series",
                                     series_title)
                            break
                        except sqlite3.OperationalError as e:
                            logging.exception(e)
        value = util.get_config_value(cursor,'series_process_interval')
        time.sleep(int(value))

def process_movie_queue():
    "handle movie queues"
    connect = sqlite3.connect(settings.DATABASE_PATH)
    cursor = connect.cursor()
    connect.execute("PRAGMA journal_mode=WAL")
    while 1:
        check_upcoming_queue(connect, cursor)
        cursor.execute("SELECT title,mq.id,mtl.link,watch_queue_status_id FROM "+
               "movie_torrent_links as mtl "+
               " join movie_queue as mq "+
               "on mtl.movie_id=mq.movie_id "+
               "join movies on mtl.movie_id=movies.id ")
        new_queue = cursor.fetchall()
        for (movie_title, queue_id, torrent_url, watch_id) in  new_queue:
            if watch_id == 1:
                logging.debug("new movie in queue, downloading torrent")
                if util.fetch_torrent(torrent_url, movie_title):
                    try:
                        connect.execute("UPDATE movie_queue set watch_queue_status_id=2 where id=?",
                            (queue_id,))
                        connect.commit()
                    except sqlite3.OperationalError as e:
                        logging.exception(e)
            elif watch_id == 2:
                if os.path.isdir(settings.INCOMPLETE_DIRECTORY+movie_title):
                    try:
                        connect.execute("UPDATE movie_queue set watch_queue_status_id=3 where id=?",
                            (queue_id,))
                        connect.commit()
                    except sqlite3.OperationalError as e:
                        logging.exception(e)
            elif watch_id == 3:
                if os.path.isdir(settings.COMPLETE_DIRECTORY+movie_title):
                    try:
                        connect.execute("UPDATE movie_queue set watch_queue_status_id=4 where id=?",
                            (queue_id,))
                        connect.commit()
                        announce("Torrent Downloaded", "Movie",
                                 movie_title)
                    except sqlite3.OperationalError as e:
                        logging.exception(e)
            else:
                logging.debug('no new queues')
        value = util.get_config_value(cursor,'movie_process_interval')
        time.sleep(int(value))
        

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

def fetch_kickass_file():
    try:
        kickass_file = urlopen("https://kickass.so/hourlydump.txt.gz")
        with gzip.open(kickass_file,'r') as gzip_file:
            with open(settings.KICKASS_FILE,'wb') as dump_file:
                for line in gzip_file:
                    dump_file.write(line)
        return settings.KICKASS_FILE
    except urllib.error.URLError:
        logging.debug("unable to connect to kickass")
        return settings.KICKASS_FILE
