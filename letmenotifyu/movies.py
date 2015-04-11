#!/usr/bin/python3

from urllib.request import urlopen, urlretrieve
from letmenotifyu.notify import announce
from letmenotifyu import settings
from letmenotifyu import util
from threading import Thread
from queue import Queue
import logging
import sqlite3
import json
import os
import urllib


def movie(connect, cursor):
    upcoming_movie_data = get_upcoming_movies()
    if upcoming_movie_data:
        insert_upcoming_movies(upcoming_movie_data, connect, cursor)
    released_movie_data = get_released_movies(cursor)
    if released_movie_data:
        insert_released_movies(released_movie_data, cursor, connect)


def get_upcoming_movies():
    "Get list of upcoming movies by yifi"
    try:
        yifi_url = urlopen("https://yts.to/api/v2/list_upcoming.json")
        json_data = json.loads(yifi_url.read().decode('utf-8'))
        return json_data
    except (urllib.error.URLError, urllib.error.HTTPError):
        logging.error("Unable to connect to upcoming movies api")
    except Exception as error:
        logging.exception(error)


def get_released_movies(cursor):
    "Get list of movies released by yifi"
    try:
        quality = util.get_config_value(cursor, "movie_quality")
        limit = util.get_config_value(cursor, 'max_movie_results')
        yifi_url = urlopen("https://yts.to/api/v2/list_movies.json?quality={}&limit={}".format(quality, limit))
        json_data = json.loads(yifi_url.read().decode('utf-8'))
        return json_data
    except (urllib.error.URLError, urllib.error.HTTPError):
        logging.error("unable to connect to released movies api")
    except Exception as error:
        logging.exception(error)


def get_movie_details(yify_id):
    try:
        yify_url = urlopen("https://yts.to/api/v2/movie_details.json?movie_id={}&with_cast=true".format(yify_id))
        movie_detail = json.loads(yify_url.read().decode('utf-8'))
        return movie_detail
    except (urllib.error.URLError, urllib.error.HTTPError):
        logging.warn("Unable to connect to movie detail api")
    except Exception as error:
        logging.exception(error)


def insert_movie_details(q):
    connect = sqlite3.connect(settings.DATABASE_PATH)
    cursor = connect.cursor()
    while True:
        [movie_id, yify_id] = q.get()
        movie_detail = get_movie_details(yify_id)
        if not movie_detail:
            q.task_done()
        elif movie_detail["status"] == "ok":
            try:
                connect.execute("INSERT INTO movie_details(movie_id,language,movie_rating,"\
                                    'youtube_url,description) '\
                                    'VALUES(?,?,?,?,?)',(movie_id, movie_detail["data"]['language'],
                                                         movie_detail['data']["rating"],
                                                         "https://www.youtube.com/watch?v={}".format(movie_detail["data"]["yt_trailer_code"]),
                                                         movie_detail["data"]["description_full"],))
                for actor in movie_detail["data"]["actors"]:
                    try:
                        row = connect.execute("INSERT INTO actors(name) "\
                                          'VALUES(?)',(actor["name"],))
                        connect.execute("INSERT INTO actors_movies(actor_id,movie_id) "\
                                    'VALUES(?,?)',(row.lastrowid, movie_id,))
                    except sqlite3.IntegrityError:
                        logging.debug("{} already exsists".format(actor["name"]))
                        cursor.execute("SELECT id from actors where name=?", (actor["name"],))
                        (actor_id,) = cursor.fetchone()
                        connect.execute("INSERT INTO actors_movies(actor_id,movie_id) "\
                                        'VALUES(?,?)', (actor_id, movie_id,))
                    finally:
                        connect.commit()
            except sqlite3.IntegrityError:
                logging.warn("Movie Detail already exists")
            except sqlite3.OperationalError as e:
                logging.exception(e)
                connect.rollback()
            finally:
                q.task_done()
        else:
            q.task_done()


def insert_released_movies(data, cursor, db):
    "insert new movies"
    if not data:
        return
    elif data["status"] == "error":
        return
    else:
        released_data = movie_compare(cursor, "movies", data["data"]["movies"])
        q = Queue(maxsize=0)
        details_worker = Thread(target=insert_movie_details, args=(q,))
        details_worker.setDaemon(True)
        details_worker.start()
        for movie_detail in released_data:
            if fetch_image(movie_detail["medium_cover_image"], movie_detail['title']):
                try:
                    genre_id = get_movie_genre(movie_detail["genres"][0], cursor, db)
                    row = db.execute("INSERT INTO movies(genre_id,title,link,date_added,movie_id,year)"+
                                 'VALUES(?,?,?,?,?,?)',
                           (genre_id,
                            movie_detail['title'],
                            "http://www.imdb.com/title/{}".format(movie_detail["imdb_code"]),
                            movie_detail["date_uploaded"],
                            movie_detail["id"],
                           movie_detail["year"],))
                    db.execute("INSERT INTO movie_torrent_links(movie_id,link,hash_sum) VALUES(?,?,?)",
                           (row.lastrowid, movie_detail["torrents"][0]["url"], movie_detail["torrents"][0]["hash"],))
                    db.execute("INSERT INTO movie_images(title,path) VALUES(?,?)",
                               (movie_detail['title'], movie_detail['title']+".jpg",))
                    q.put([row.lastrowid, movie_detail["id"]])
                    db.execute("DELETE FROM upcoming_movies WHERE title IN (SELECT title FROM movies)")
                    db.commit()
                    announce('Newly Released Movie', "{} ({})".format(movie_detail["title"], movie_detail["genres"][0]),
                         "http://www.imdb.com/title/{}".format(movie_detail["imdb_code"]))
                except sqlite3.IntegrityError:
                    logging.info("image for {}  already exists in database".format(movie_detail['title']))
                except Exception as e:
                    db.rollback()
                    logging.exception(e)
        q.join()


def insert_upcoming_movies(movie_data, db, cursor):
    "insert upcoming new movies"
    new_movie_data = movie_compare(cursor, "upcoming_movies", movie_data["data"]["upcoming_movies"])
    if new_movie_data:
        for movie_detail in new_movie_data:
            if fetch_image(movie_detail["medium_cover_image"], movie_detail["title"]):
                try:
                    db.execute("INSERT INTO movie_images(title,path) VALUES(?,?)",
                               (movie_detail['title'], movie_detail['title']+".jpg",))
                    db.execute("INSERT INTO upcoming_movies(title,link) VALUES(?,?)",
                       (movie_detail["title"],
                        "http://www.imdb.com/title/{}".format(movie_detail["imdb_code"]),))
                    db.commit()
                    announce('Upcoming Movie', movie_detail["title"],
                         "http://www.imdb.com/title/{}".format(movie_detail["imdb_code"]))
                except sqlite3.IntegrityError:
                    logging.info("image for {}  already exists in database".format(movie_detail['title']))
                except Exception as error:
                    db.rollback()
                    logging.exception(error)
    else:
        logging.debug("no new upcoming movies")


def fetch_image(image_url, title,):
    "fetch image"
    if os.path.isfile(settings.IMAGE_PATH+title+".jpg"):
        logging.debug("Image file for {} already downloaded".format(title))
        return True
    else:
        try:
            urlretrieve(image_url, settings.IMAGE_PATH+title+".jpg")
            logging.debug("imaged fetched for {}".format(title))
            return True
        except Exception as e:
            logging.exception(e)
            return False


def movie_compare(cursor, table, new_data):
    "compare new movie list to current database"
    new_movie_data = []
    cursor.execute("SELECT title from "+table)
    old_movie_data = [x[0] for x in cursor.fetchall()]
    for movie_data in new_data:
        if movie_data["title"] not in old_movie_data:
            new_movie_data.append(movie_data)
    return new_movie_data


def get_movie_genre(genre, cursor, db):
    cursor.execute("SELECT Id FROM genre where genre=?", (genre,))
    if cursor.fetchone() is None:
        logging.debug("genre does not exist yet")
        row = db.execute("INSERT INTO genre(genre) VALUES(?)", (genre,))
        genre_id = row.lastrowid
        return genre_id
    else:
        logging.debug('genre exists')
        cursor.execute("SELECT Id FROM genre where genre=?", (genre,))
        (genre_id,) = cursor.fetchone()
        return int(genre_id)
