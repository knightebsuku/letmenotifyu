#!/usr/bin/python3

import psycopg2
import logging
import time
import gzip
import os
import urllib
import glob

from . import settings, util, kickass, yify
from .movies import movie
from .series import series
from threading import Thread
from urllib.request import urlopen


def update():
    "check for updates for movies and series"
    while True:
        connect = psycopg2.connect(host=settings.DB_HOST,
                                        database=settings.DB_NAME,
                                        port=settings.DB_PORT,
                                        user=settings.DB_USER,
                                        password=settings.DB_PASSWORD)
        cursor = connect.cursor()
        logging.debug("Checking for new episodes and new movie releases")
        movie(connect, cursor)
        series(connect, cursor)
        value = util.get_config_value(cursor, 'update_interval')
        connect.close()
        time.sleep(float(value)*60)


def process_series_queue():
    "handle the series queues"
    while True:
        connect = psycopg2.connect(host=settings.DB_HOST,
                                        database=settings.DB_NAME,
                                        port=settings.DB_PORT,
                                        user=settings.DB_USER,
                                        password=settings.DB_PASSWORD)
        cursor = connect.cursor()
        kickass_file = fetch_kickass_file(cursor)
        cursor.execute("SELECT title, series_queue.id, episode_name, watch_queue_status_id "\
                       'FROM  series_queue join series ON series_id=series.id and watch_queue_status_id <> 4')
        for (title, queue_id, ep_name, watch_id) in cursor.fetchall():
            series_titles = title.replace(" ", ".")
            if watch_id == 1:
                logging.info("fetching episode torrent for {}".format(title))
                try:
                    episode_title, episode_link = kickass.search_episode(kickass_file,
                                                                        title,
                                                                        ep_name,
                                                                        "HDTV x264-(LOL|KILLERS|ASAP|2HD|FUM)")
                    if util.fetch_torrent(episode_link.replace("\n", ""), episode_title):
                        try:
                            cursor.execute("INSERT INTO series_torrent_links(series_queue_id, link) VALUES(%s,%s)",
                                (queue_id, episode_link,))
                            cursor.execute("UPDATE series_queue SET watch_queue_status_id=2 WHERE id=%s",
                                (queue_id,))
                            connect.commit()
                        except psycopg2.IntegrityError:
                            connect.rollback()
                            logging.warn("torrent link for {} already exists".format(title))
                except TypeError as e:
                    logging.exception(e)
                    pass
            elif watch_id == 2:
                for dirs in os.listdir(settings.INCOMPLETE_DIRECTORY):
                    if dirs.startswith(series_titles):
                        try:
                            cursor.execute("UPDATE series_queue SET watch_queue_status_id=3 WHERE id=%s",
                                        (queue_id,))
                            connect.commit()
                            break
                        except psycopg2.OperationalError as error:
                            connect.rollback()
                            logging.exception(error)
                            break
            elif watch_id == 3:
                for dirs in os.listdir(settings.COMPLETE_DIRECTORY):
                    if dirs.startswith(series_titles):
                        try:
                            cursor.execute("UPDATE series_queue SET watch_queue_status_id=4 WHERE id=%s",
                                            (queue_id,))
                            connect.commit()
                            break
                        except psycopg2.OperationalError as e:
                            connect.rollback()
                            logging.exception(e)
                            break
        value = util.get_config_value(cursor, 'series_process_interval')
        connect.close()
        time.sleep(float(value)*60)


def process_movie_queue():
    "handle movie queues"
    while True:
        connect = psycopg2.connect(host=settings.DB_HOST,
                                        database=settings.DB_NAME,
                                        port=settings.DB_PORT,
                                        user=settings.DB_USER,
                                        password=settings.DB_PASSWORD)
        cursor = connect.cursor()
        check_upcoming_queue(connect, cursor)
        cursor.execute("SELECT title,mq.id,mtl.link,watch_queue_status_id FROM "\
               "movie_torrent_links as mtl "\
               " join movie_queue as mq "\
               "on mtl.movie_id=mq.movie_id "\
               "join movies on mtl.movie_id=movies.id and watch_queue_status_id <> 4 order by mq.id ")
        for (movie_title, queue_id, torrent_url, watch_id) in cursor.fetchall():
            if watch_id == 1:
                logging.info("downloading torrent for {}".format(movie_title))
                if util.fetch_torrent(torrent_url, movie_title):
                    try:
                        cursor.execute("UPDATE movie_queue SET watch_queue_status_id=2 WHERE id=%s",
                            (queue_id,))
                        connect.commit()
                    except psycopg2.OperationalError as error:
                        connect.rollback()
                        logging.exception(error)
            elif watch_id == 2:
                if glob.glob("{}*".format(settings.INCOMPLETE_DIRECTORY+movie_title)):
                    try:
                        logging.debug("{} on status 2, moving to status 3".format(movie_title))
                        cursor.execute("UPDATE movie_queue SET watch_queue_status_id=3 WHERE id=%s",
                            (queue_id,))
                        connect.commit()
                    except psycopg2.OperationalError as error:
                        connect.rollback()
                        logging.exception(error)
            elif watch_id == 3:
                if glob.glob("{}*".format(settings.COMPLETE_DIRECTORY+movie_title)):
                    try:
                        logging.debug("{} on status 3, moving to status 4".format(movie_title))
                        cursor.execute("UPDATE movie_queue SET watch_queue_status_id=4 WHERE id=%s",
                            (queue_id,))
                        connect.commit()
                    except psycopg2.OperationalError as error:
                        connect.rollback()
                        logging.exception(error)
            else:
                logging.debug('no movies in queues')
        value = util.get_config_value(cursor, 'movie_process_interval')
        connect.close()
        time.sleep(float(value)*60)


def movie_details_process():
    "add movie details"
    while True:
        connect = psycopg2.connect(host=settings.DB_HOST,
                                        database=settings.DB_NAME,
                                        port=settings.DB_PORT,
                                        user=settings.DB_USER,
                                        password=settings.DB_PASSWORD)
        cursor = connect.cursor()
        cursor.execute('SELECT movies.id,yify_id FROM movies LEFT OUTER JOIN  movie_details '\
                       'ON movies.id=movie_details.movie_id WHERE movie_details.movie_id is NULL')
        for (movie_id, yify_id) in cursor.fetchall():
            logging.debug("getting movie details for {}".format(movie_id))
            movie_detail = yify.get_movie_details(yify_id)
            if not movie_detail:
                pass
            elif movie_detail["status"] == "ok":
                try:
                    cursor.execute("INSERT INTO movie_details(movie_id,language,movie_rating,"\
                                    'youtube_url,description) '\
                                    'VALUES(%s,%s,%s,%s,%s)',
                                (movie_id, movie_detail["data"]['language'],
                                                         movie_detail['data']["rating"],
                                                         movie_detail["data"]["yt_trailer_code"],
                                                         movie_detail["data"]["description_full"],))
                    check_actors(movie_detail['data']['actors'], movie_id, cursor)
                    connect.commit()
                except psycopg2.IntegrityError as e:
                    connect.rollback()
                    logging.warn("Movie Detail already exists")
                    logging.exception(e)
                except psycopg2.OperationalError as e:
                    connect.rollback()
                    logging.exception(e)
        connect.close()
        time.sleep(600)


def check_upcoming_queue(connect, cursor):
    "move upcoming queue movie to movie_queue"
    cursor.execute("SELECT title FROM upcoming_queue")
    data = cursor.fetchall()
    for (title,) in data:
        cursor.execute("SELECT id FROM movies WHERE title=%s", (title,))
        if cursor.fetchone():
            try:
                cursor.execute("INSERT INTO movie_queue(movie_id,watch_queue_status_id) "\
                            "SELECT movies.id,watch_queue_status.id FROM movies,watch_queue_status "\
                            "WHERE movies.title=%s AND watch_queue_status.name='new'", (title,))
                cursor.execute("DELETE FROM upcoming_queue WHERE title=%s", (title,))
                connect.commit()
                logging.info("moved {} to movie_queue".format(title))
            except psycopg2.IntegrityError:
                connect.rollback()
                logging.info("{} already  exists in movie_queue".format(title))
                cursor.execute("DELETE FROM upcoming_queue WHERE title=%s", (title,))


def fetch_kickass_file(cursor):
    "fetch kickass dump file"
    cursor.execute("SELECT * FROM series_queue WHERE watch_queue_status_id=1")
    if cursor.fetchall():
        logging.debug("episode in status new, need to fetch kickass file")
        try:
            kickass_file = urlopen("https://kat.cr/hourlydump.txt.gz")
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


def check_actors(actor_details, movie_id, cursor):
    "Check if actor exists or not"
    for actor in actor_details:
        cursor.execute("SELECT id from actors WHERE name=%s", (actor['name'],))
        if cursor.fetchone():
            cursor.execute("SELECT id from actors WHERE name=%s", (actor['name'],))
            (actor_id,) = cursor.fetchone()
            cursor.execute("INSERT INTO actors_movies(actor_id,movie_id) "\
                                        'VALUES(%s,%s)', (actor_id, movie_id,))
        else:
            cursor.execute("INSERT INTO actors(name) "\
                                          'VALUES(%s) RETURNING id',(actor["name"],))
            lastrowid = cursor.fetchone()[0]
            cursor.execute("INSERT INTO actors_movies(actor_id,movie_id) "\
                                    'VALUES(%s,%s)',(lastrowid, movie_id,))


def start_threads():
    "start all threads and processes"
    all_update = Thread(target=update)
    all_update.setDaemon(True)
    all_update.start()
