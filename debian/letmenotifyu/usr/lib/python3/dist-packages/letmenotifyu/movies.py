#!/usr/bin/python3

from urllib.request import urlopen, urlretrieve
from letmenotifyu.notify import announce
from letmenotifyu import settings
from letmenotifyu import util
from threading import Thread
from queue import Queue
import logging
import psycopg2
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
        return json.loads(yifi_url.read().decode('utf-8'))
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
        return json.loads(yifi_url.read().decode('utf-8'))
    except (urllib.error.URLError, urllib.error.HTTPError):
        logging.error("unable to connect to released movies api")
    except Exception as error:
        logging.exception(error)


def get_movie_details(yify_id):
    try:
        yify_url = urlopen("https://yts.to/api/v2/movie_details.json?movie_id={}&with_cast=true".format(yify_id))
        return json.loads(yify_url.read().decode('utf-8'))
    except (urllib.error.URLError, urllib.error.HTTPError):
        logging.warn("Unable to connect to movie detail api")
    except Exception as error:
        logging.exception(error)


def insert_movie_details(q):
    connect = psycopg2.connect(host=settings.DB_HOST,
                                        database=settings.DB_NAME,
                                        port=settings.DB_PORT,
                                        user=settings.DB_USER,
                                        password=settings.DB_PASSWORD)
    cursor = connect.cursor()
    while True:
        [movie_id, yify_id] = q.get()
        movie_detail = get_movie_details(yify_id)
        if not movie_detail:
            q.task_done()
        elif movie_detail["status"] == "ok":
            try:
                cursor.execute("INSERT INTO movie_details(movie_id,language,movie_rating,"\
                                    'youtube_url,description) '\
                                    'VALUES(%s,%s,%s,%s,%s)',
                                (movie_id, movie_detail["data"]['language'],
                                                         movie_detail['data']["rating"],
                                                         "https://www.youtube.com/watch?v={}".format(movie_detail["data"]["yt_trailer_code"]),
                                                         movie_detail["data"]["description_full"],))
                check_actors(movie_detail['data']['actors'], movie_id, cursor)
                connect.commit()
            except psycopg2.IntegrityError:
                connect.rollback()
                logging.warn("Movie Detail already exists")
            except psycopg2.OperationalError as e:
                connect.rollback()
                logging.exception(e)
                q.put([movie_id, yify_id])
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
                    cursor.execute("INSERT INTO movies(genre_id,title,link,date_added,yify_id,year)"+
                                 'VALUES(%s,%s,%s,%s,%s,%s) RETURNING id',
                           (genre_id,
                            movie_detail['title'],
                            "http://www.imdb.com/title/{}".format(movie_detail["imdb_code"]),
                            movie_detail["date_uploaded"],
                            movie_detail["id"],
                           movie_detail["year"],))
                    row_id = cursor.fetchone()[0]
                    cursor.execute("INSERT INTO movie_torrent_links(movie_id,link,hash_sum) VALUES(%s,%s,%s)",
                           (row_id, movie_detail["torrents"][0]["url"], movie_detail["torrents"][0]["hash"],))
                    if image_record_exists(movie_detail['title'],cursor):
                        pass
                    else:
                        cursor.execute("INSERT INTO movie_images(title,path) VALUES(%s,%s)",
                               (movie_detail['title'], movie_detail['title']+".jpg",))
                    q.put([row_id, movie_detail["id"]])
                    cursor.execute("DELETE FROM upcoming_movies WHERE title IN (SELECT title FROM movies)")
                    db.commit()
                    announce('Newly Released Movie', "{} ({})".format(movie_detail["title"], movie_detail["genres"][0]),
                         "http://www.imdb.com/title/{}".format(movie_detail["imdb_code"]))
                except psycopg2.IntegrityError as e:
                    db.rollback()
                    logging.exception(e)
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
                    cursor.execute("INSERT INTO movie_images(title,path) VALUES(%s,%s)",
                               (movie_detail['title'], movie_detail['title']+".jpg",))
                    cursor.execute("INSERT INTO upcoming_movies(title,link) VALUES(%s,%s)",
                       (movie_detail["title"],
                        "http://www.imdb.com/title/{}".format(movie_detail["imdb_code"]),))
                    db.commit()
                    announce('Upcoming Movie', movie_detail["title"],
                         "http://www.imdb.com/title/{}".format(movie_detail["imdb_code"]))
                except psycopg2.IntegrityError as e:
                    db.rollback()
                    logging.exception(e)
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
    cursor.execute("SELECT title FROM "+table)
    old_movie_data = [x[0] for x in cursor.fetchall()]
    for movie_data in new_data:
        if movie_data["title"] not in old_movie_data:
            new_movie_data.append(movie_data)
    return new_movie_data


def get_movie_genre(genre, cursor, db):
    cursor.execute("SELECT id FROM genre WHERE genre=%s", (genre,))
    if cursor.fetchone() is None:
        logging.debug("genre does not exist yet")
        cursor.execute("INSERT INTO genre(genre) VALUES(%s) RETURNING id", (genre,))
        genre_id = cursor.fetchone()[0]
        return genre_id
    else:
        logging.debug('genre exists')
        cursor.execute("SELECT id FROM genre WHERE genre=%s", (genre,))
        (genre_id,) = cursor.fetchone()
        return int(genre_id)


def image_record_exists(movie_title, cursor):
    cursor.execute("SELECT id from movie_images WHERE title=%s",(movie_title,))
    if cursor.fetchone():
        return True


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
