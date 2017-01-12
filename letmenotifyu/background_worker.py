import logging
import time
import sqlite3
import json

from . import settings, util, yify, transmission, kickass
from .movies import Movie
from .series import Series
from threading import Thread
from requests.exceptions import ConnectionError

log = logging.getLogger(__name__)


def movie_update():
    """
    check for any new movies
    """
    try:
        json_yify = yify.new_movies()
        if json_yify['status'] == 'error':
            log.error("Error connecting to yify json api")
        else:
            movie_list = json_yify['data']['movies']
    except(ConnectionError):
        log.error("Unable to connect to yify site")
    except json.decoder.JSONDecodeError as error:
        log.exception(error)
    else:
        for m in movie_list:
            json_movie = Movie(m)
            if json_movie.poster():
                json_movie.commit()


def series_update():
    "Check for any new series episodes"
    log.info("checking for series updates")
    series = Series()
    series.update()


def update():
    """
    Check for new movie and series episode releases
    """
    while True:
        connect = sqlite3.connect(settings.GENERAL_DB)
        cursor = connect.cursor()
        movie_update()
        series_update()
        interval = util.get_config_value(cursor, 'update_interval')
        connect.close()
        time.sleep(float(interval))


def process_series_queue():
    """
    Check for new series epsiodes which are on status 1(NEW) and fetch
    the magent links and send to transmission
    """
    while True:
        connect = sqlite3.connect(settings.SERIES_DB, timeout=10)
        cursor = connect.cursor()
        cursor.execute(settings.SQLITE_WAL_MODE)

        cursor.execute("SELECT title, series_queue.id,"
                       "episode_name, watch_queue_status_id "
                       "FROM series_queue JOIN series ON series_id=series.id "
                       "AND watch_queue_status_id <> 4")
        for (title, queue_id, ep_name, watch_id) in cursor.fetchall():
            if watch_id == 1:
                log.info("fetching episode magnet for {}".format(title))
                magnet_url = kickass.fetch_episode_search_results(title, ep_name)
                if magnet_url is not None:
                    try:
                        torrent_hash, torrent_name = transmission.add_torrent(
                            magnet_url)
                        cursor.execute("INSERT INTO series_torrent_links("
                                       "series_queue_id, link,"
                                       "transmission_hash, torrent_name) "
                                       "VALUES(?,?,?,?)",
                                       (queue_id,
                                        magnet_url,
                                        torrent_hash,
                                        torrent_name,))
                        cursor.execute("UPDATE series_queue SET "
                                       "watch_queue_status_id=2 "
                                       "WHERE id=?", (queue_id,))
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
    "handle all movies in the queues"
    while True:
        connect = sqlite3.connect(settings.MOVIE_DB, timeout=10)
        cursor = connect.cursor()
        cursor.execute(settings.SQLITE_WAL_MODE)

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
                            torrent_file_path)
                        log.debug("updating details for movie {}".format(
                            movie_title))
                        cursor.execute("UPDATE movie_torrent_links SET "
                                       "transmission_hash=?,"
                                       "torrent_name=? WHERE link=?",
                                       (torrent_hash, torrent_name,
                                        torrent_url,))
                        cursor.execute("UPDATE movie_queue SET "
                                       "watch_queue_status_id=2 WHERE id=?",
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
        connect = sqlite3.connect(settings.MOVIE_DB, timeout=10)
        cursor = connect.cursor()
        cursor.execute(settings.SQLITE_WAL_MODE)
        cursor.execute('SELECT movies.id,yify_id FROM movies '
                       'LEFT OUTER JOIN  movie_details '
                       'ON movies.id=movie_details.movie_id '
                       'WHERE movie_details.movie_id is NULL')
        for (movie_id, yify_id) in cursor.fetchall():
            log.debug("getting movie details for {}".format(movie_id))
            movie_detail = yify.movie_details(yify_id)
            if not movie_detail:
                pass
            elif movie_detail["status"] == "ok":
                try:
                    detail = movie_detail['data']['movie']
                    cursor.execute("INSERT INTO movie_details("
                                   "movie_id,language,movie_rating,"
                                   'youtube_url,description) '
                                   'VALUES(?,?,?,?,?)',
                                   (movie_id,
                                    detail['language'],
                                    detail["rating"],
                                    detail["yt_trailer_code"],
                                    detail["description_full"],))
                    connect.commit()
                except sqlite3.IntegrityError as e:
                    connect.rollback()
                    log.warn("Movie Detail already exists")
                    log.exception(e)
                except sqlite3.OperationalError as e:
                    connect.rollback()
                    log.exception(e)
        connect.close()
        time.sleep(300)


def update_thread():
    thread = Thread(target=update)
    thread.setDaemon(True)
    thread.start()
