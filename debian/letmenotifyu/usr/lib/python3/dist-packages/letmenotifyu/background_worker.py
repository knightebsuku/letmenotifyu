#!/usr/bin/python3

import sqlite3
import logging
import time
import gzip
import os
import urllib
import glob
from letmenotifyu import settings
from letmenotifyu.movies import movie
from letmenotifyu.series import series
from letmenotifyu import util
from letmenotifyu import kickass
from threading import Thread
from urllib.request import urlopen


def start_threads():
    "start all threads"
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
        logging.debug("Checking for new episodes and new movie releases")
        connect = sqlite3.connect(settings.DATABASE_PATH)
        cursor = connect.cursor()
        movie(connect, cursor)
        series(connect, cursor)
        value = util.get_config_value(cursor, 'update_interval')
        connect.close()
        time.sleep(float(value)*3600)


def process_series_queue():
    "handle the series queues"
    connect = sqlite3.connect(settings.DATABASE_PATH)
    cursor = connect.cursor()
    while 1:
        api_file = fetch_kickass_file(cursor)
        cursor.execute("SELECT title, series_queue.id, episode_name,watch_queue_status_id "\
                       'FROM  series_queue join series ON series_id=series.id')
        queues = cursor.fetchall()
        for (title, queue_id, ep_name, watch_id) in queues:
            if watch_id == 1:
                logging.info("fetching episode torrent for {}".format(title))
                try:
                    (_, series_title, _, _, episode_link) = kickass.search_episode(api_file, title, ep_name,
                                                                                   "HDTV x264-(LOL|KILLERS|ASAP)")
                    if util.fetch_torrent(episode_link.replace("\n",""), series_title):
                        try:
                            connect.execute("INSERT INTO series_torrent_links(series_queue_id,link) VALUES(?,?)",
                                (queue_id, episode_link,))
                            connect.execute("UPDATE series_queue set watch_queue_status_id=2 where id=?",
                                (queue_id,))
                            connect.commit()
                        except sqlite3.IntegrityError:
                            logging.warn("torrent link for {} already exists".format(title))
                except TypeError:
                    pass
            elif watch_id == 2:
                series_title = title.replace(" ", ".")
                for dirs in os.listdir(settings.INCOMPLETE_DIRECTORY):
                    if dirs.startswith(series_title):
                        try:
                            connect.execute("UPDATE series_queue SET watch_queue_status_id=3 WHERE id=?",
                                        (queue_id,))
                            connect.commit()
                            break
                        except sqlite3.OperationalError as error:
                            logging.exception(error)
                            break
            elif watch_id == 3:
                series_title = title.replace(" ", ".")
                for dirs in os.listdir(settings.COMPLETE_DIRECTORY):
                    if dirs.startswith(series_title):
                        try:
                            connect.execute("UPDATE series_queue set watch_queue_status_id=4 where id=?",
                                            (queue_id,))
                            connect.commit()
                            break
                        except sqlite3.OperationalError as e:
                            logging.exception(e)
                            break
        cursor.execute("PRAGMA wal_checkpoint(PASSIVE)")
        value = util.get_config_value(cursor, 'series_process_interval')
        time.sleep(float(value)*3600)


def process_movie_queue():
    "handle movie queues"
    connect = sqlite3.connect(settings.DATABASE_PATH)
    cursor = connect.cursor()
    while 1:
        check_upcoming_queue(connect, cursor)
        cursor.execute("SELECT title,mq.id,mtl.link,watch_queue_status_id FROM "\
               "movie_torrent_links as mtl "\
               " join movie_queue as mq "\
               "on mtl.movie_id=mq.movie_id "\
               "join movies on mtl.movie_id=movies.id order by mq.id ")
        for (movie_title, queue_id, torrent_url, watch_id) in cursor.fetchall():
            if watch_id == 1:
                logging.info("downloading torrent for {}".format(movie_title))
                if util.fetch_torrent(torrent_url, movie_title):
                    try:
                        connect.execute("UPDATE movie_queue set watch_queue_status_id=2 where id=?",
                            (queue_id,))
                        connect.commit()
                    except sqlite3.OperationalError as error:
                        logging.exception(error)
            elif watch_id == 2:
                if glob.glob("{}*".format(settings.INCOMPLETE_DIRECTORY+movie_title)):
                    try:
                        logging.debug("{} on status 2, moving to status 3".format(movie_title))
                        connect.execute("UPDATE movie_queue set watch_queue_status_id=3 where id=?",
                            (queue_id,))
                        connect.commit()
                    except sqlite3.OperationalError as error:
                        logging.exception(error)
            elif watch_id == 3:
                if glob.glob("{}*".format(settings.COMPLETE_DIRECTORY+movie_title)):
                    try:
                        logging.debug("{} on status 3, moving to status 4".format(movie_title))
                        connect.execute("UPDATE movie_queue set watch_queue_status_id=4 where id=?",
                            (queue_id,))
                        connect.commit()
                    except sqlite3.OperationalError as error:
                        logging.exception(error)
            else:
                logging.debug('no movies in queues')
        value = util.get_config_value(cursor, 'movie_process_interval')
        time.sleep(float(value)*3600)

def check_upcoming_queue(connect,cursor):
    "move upcoming queue movie to movie_queue"
    cursor.execute("SELECT title FROM upcoming_queue")
    data = cursor.fetchall()
    for (title,) in data:
        cursor.execute("SELECT id FROM movies WHERE title=?", (title,))
        if cursor.fetchone():
            try:
                cursor.execute("INSERT INTO movie_queue(movie_id,watch_queue_status_id) "\
                            "SELECT movies.id,watch_queue_status.id FROM movies,watch_queue_status "\
                            "WHERE movies.title=? AND watch_queue_status.name='new'", (title,))
                connect.execute("DELETE FROM upcoming_queue WHERE title=?", (title,))
                connect.commit()
                logging.info("moved {} to movie_queue".format(title))
            except sqlite3.IntegrityError:
                logging.info("{} already  exists in movie_queue".format(title))
                connect.execute("DELETE FROM upcoming_queue WHERE title=?", (title,))


def fetch_kickass_file(cursor):
    "fetch kickass dump file"
    cursor.execute("SELECT * FROM series_queue where watch_queue_status_id=1")
    if cursor.fetchall():
        logging.debug("episode in status new, need to fetch kickass file")
        try:
            kickass_file = urlopen("https://kickass.to/hourlydump.txt.gz")
            with gzip.open(kickass_file, 'r') as gzip_file:
                with open(settings.KICKASS_FILE, 'wb') as dump_file:
                    for line in gzip_file:
                        dump_file.write(line)
            return settings.KICKASS_FILE
        except urllib.error.URLError:
            logging.warn("unable to connect to kickass to fetch dump file")
            return settings.KICKASS_FILE
    else:
        logging.debug("no episodes in new status")
        return settings.KICKASS_FILE
