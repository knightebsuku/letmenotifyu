#!/usr/bin/python3

import psycopg2
import logging
import time

from . import settings, util, yify, transmission, piratebay
from .movies import movie
from .series import series
from threading import Thread

log = logging.getLogger(__name__)


def update():
    """
    Check for new movie releases
    Check for new series episodes
    """
    while True:
        connect = psycopg2.connect(host=settings.DB_HOST,
                                   database=settings.DB_NAME,
                                   port=settings.DB_PORT,
                                   user=settings.DB_USER,
                                   password=settings.DB_PASSWORD)
        cursor = connect.cursor()
        log.debug("checking for new movies")
        movie(connect, cursor)
        log.debug("checking for new series episodes")
        series(connect, cursor)
        value = util.get_config_value(cursor, 'update_interval')
        connect.close()
        time.sleep(float(value)*60)


def process_series_queue():
    """
    Check for new series epsiodes which are on status 1(NEW) and fetch
    the magent links and send to transmission
    """
    while True:
        connect = psycopg2.connect(host=settings.DB_HOST,
                                   database=settings.DB_NAME,
                                   port=settings.DB_PORT,
                                   user=settings.DB_USER,
                                   password=settings.DB_PASSWORD)
        cursor = connect.cursor()
        cursor.execute("SELECT title, series_queue.id,"
                       "episode_name, watch_queue_status_id "
                       "FROM series_queue JOIN series ON series_id=series.id "
                       " AND watch_queue_status_id <> 4")
        for (title, queue_id, ep_name, watch_id) in cursor.fetchall():
            if watch_id == 1:
                log.info("fetching episode magnet for {}".format(title))
                magnet_url = piratebay.episode_magnet_link(title, ep_name)
                if magnet_url is not None:
                    try:
                        torrent_hash, torrent_name = transmission.add_torrent(
                            magnet_url, cursor)
                        cursor.execute("INSERT INTO series_torrent_links("
                                       "series_queue_id, link,"
                                       "transmission_hash, torrent_name) "
                                       "VALUES(%s,%s,%s,%s)",
                                       (queue_id,
                                        magnet_url,
                                        torrent_hash,
                                        torrent_name,))
                        cursor.execute("UPDATE series_queue SET "
                                       "watch_queue_status_id=2 "
                                       "WHERE id=%s", (queue_id,))
                        connect.commit()
                    except Exception as e:
                        connect.rollback()
                        log.exception(e)
            else:
                transmission.check_episode_status(
                    watch_id, queue_id, cursor, connect)
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
        cursor.execute("SELECT title,mq.id,mtl.link,transmission_hash, "
                       "watch_queue_status_id "
                       "FROM "
                       "movie_torrent_links AS mtl "
                       "JOIN movie_queue AS mq "
                       "ON mtl.movie_id=mq.movie_id "
                       "JOIN movies ON mtl.movie_id=movies.id "
                       "AND watch_queue_status_id <> 4 "
                       "ORDER BY mq.id ")
        for (movie_title, queue_id, torrent_url,
             transmission_hash, watch_id) in cursor.fetchall():
            if watch_id == 1:
                log.info("downloading torrent for {}".format(movie_title))
                (downloaded, torrent_file_path) = util.fetch_torrent(
                    torrent_url, movie_title)
                if downloaded:
                    try:
                        torrent_hash, torrent_name = transmission.add_torrent(
                            torrent_file_path, cursor)
                        log.debug("updating details for movie {}".format(
                            movie_title))
                        cursor.execute("UPDATE movie_torrent_links SET "
                                       "transmission_hash=%s,"
                                       "torrent_name=%s WHERE link=%s",
                                       (torrent_hash, torrent_name,
                                        torrent_url,))
                        cursor.execute("UPDATE movie_queue SET "
                                       "watch_queue_status_id=2 WHERE id=%s",
                                       (queue_id,))
                        connect.commit()
                    except Exception as e:
                        log.exception(e)
            else:
                transmission.check_movie_status(
                    watch_id, transmission_hash, cursor, connect)
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
        cursor.execute('SELECT movies.id,yify_id FROM movies '
                       'LEFT OUTER JOIN  movie_details '
                       'ON movies.id=movie_details.movie_id '
                       'WHERE movie_details.movie_id is NULL')
        for (movie_id, yify_id) in cursor.fetchall():
            log.debug("getting movie details for {}".format(movie_id))
            movie_detail = yify.get_movie_details(yify_id)
            if not movie_detail:
                pass
            elif movie_detail["status"] == "ok":
                try:
                    cursor.execute("INSERT INTO movie_details("
                                   "movie_id,language,movie_rating,"
                                   'youtube_url,description) '
                                   'VALUES(%s,%s,%s,%s,%s)',
                                   (movie_id, movie_detail["data"]['language'],
                                    movie_detail['data']["rating"],
                                    movie_detail["data"]["yt_trailer_code"],
                                    movie_detail["data"]["description_full"],))
                    check_actors(movie_detail['data']['actors'],
                                 movie_id, cursor)
                    connect.commit()
                except psycopg2.IntegrityError as e:
                    connect.rollback()
                    log.warn("Movie Detail already exists")
                    log.exception(e)
                except psycopg2.OperationalError as e:
                    connect.rollback()
                    log.exception(e)
        connect.close()
        time.sleep(100)


def check_actors(actor_details, movie_id, cursor):
    "Check if actor exists or not"
    for actor in actor_details:
        cursor.execute("SELECT id from actors WHERE name=%s", (actor['name'],))
        if cursor.fetchone():
            cursor.execute("SELECT id from actors WHERE name=%s",
                           (actor['name'],))
            (actor_id,) = cursor.fetchone()
            cursor.execute("INSERT INTO actors_movies(actor_id,movie_id) "
                           'VALUES(%s,%s)', (actor_id, movie_id,))
        else:
            cursor.execute("INSERT INTO actors(name) "
                           'VALUES(%s) RETURNING id', (actor["name"],))
            lastrowid = cursor.fetchone()[0]
            cursor.execute("INSERT INTO actors_movies(actor_id,movie_id) "
                           'VALUES(%s,%s)', (lastrowid, movie_id,))


def start_threads():
    "start all threads and processes"
    all_update = Thread(target=update)
    all_update.setDaemon(True)
    all_update.start()
