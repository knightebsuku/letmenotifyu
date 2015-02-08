#!/usr/bin/python3

from urllib.request import Request, urlopen
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
        yifi_url = urlopen("https://yts.re/api/v2/list_upcoming.json")
        json_data = json.loads(yifi_url.read().decode('utf-8'))
        return json_data
    except Exception:
        logging.error("Unable to connect to upcoming movies")

def get_released_movies(cursor):
    "Get list of movies released by yifi"
    try:
        quality = util.get_config_value(cursor,"movie_quality")
        limit = util.get_config_value(cursor,'max_movie_results')
        yifi_url = urlopen("https://yts.re/api/v2/list_movies.json?quality={}&limit={}".format(quality,limit))
        json_data = json.loads(yifi_url.read().decode('utf-8'))
        return json_data
    except Exception as e:
        logging.error("unable to fetch movie list")
        logging.exception(e)

def get_movie_details(yify_id):
    try:
        yify_url = urlopen("https://yts.re/api/v2/movie_details.json?movie_id={}&with_cast=true".format(yify_id))
        movie_detail = json.loads(yify_url.read().decode('utf-8'))
        return movie_detail
    except (urllib.error.URLError, urllib.error.HTTPError):
        logging.warn("Unable to download movie detail")

def insert_movie_details(q):
    connect = sqlite3.connect(settings.DATABASE_PATH)
    cursor = connect.cursor()
    while not q.empty():
        [movie_id,yify_id] = q.get()
        movie_detail = get_movie_details(yify_id)
        if not movie_detail:
            logging.warn("Unable to connect to site")
            q.task_done()
        elif movie_detail["status"] == "ok":
            try:
                connect.execute("INSERT INTO movie_details(movie_id,language,movie_rating,"+
                                    'youtube_url,description) '+
                                    'VALUES(?,?,?,?,?)',(movie_id,movie_detail['Language'],
                                                         movie_detail['data']["language"],
                                                         "https://www.youtube.com/watch?v={}".format(movie_detail["data"]["yt_trailer_code"]),
                                                         movie_detail["data"]["description_full"],))
                for actor in movie_detail["data"]["actors"]:
                    try:
                        row = connect.execute("INSERT INTO actors(name) "+
                                          'VALUES(?,?)',(actor["name"],))
                        connect.execute("INSERT INTO actors_movies(actor_id,movie_id) "+
                                    'VALUES(?,?)',(row.lastrowid, movie_id,))
                    except sqlite3.IntegrityError:
                        logging.error("record already exsists")
                        cursor.execute("SELECT id from actors where name=?", (actor["name"],))
                        (actor_id,) = cursor.fetchone()
                        connect.execute("INSERT INTO actors_movies(actor_id,movie_id) "+
                                        'VALUES(?,?)', (actor_id,movie_id,))
                        logging.info("Movie Detail complete")
                    finally:
                        connect.commit()
            except sqlite3.IntegrityError:
                logging.warn("Movie Detail already exists")
            except sqlite3.OperationalError as e:
                logging.exception(e)
            finally:
                q.task_done()
        else:
            logging.warn("Cant connect to movie_detail")
            q.task_done()
            

def insert_released_movies(data, cursor, db):
    "insert new movies"
    if not data:
        return
    elif data["status"] == "fail":
        return
    else:
        released_data = movie_compare(cursor, "movies", data["data"]["movies"])
        q = Queue(maxsize=0)
        details_worker = Thread(target=insert_movie_details, args=(q,))
        details_worker.setDaemon(True)
        details_worker.start()
        for movie_detail in released_data:
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
                insert_movie_image(movie_detail["title"], movie_detail["medium_cover_image"], db)
                q.put([row.lastrowid, movie_detail["id"]])
                db.commit()
                announce('Newly Released Movie', movie_detail["title"],
                         "http://www.imdb.com/title/{}".format(movie_detail["imdb_code"]))
            except Exception as e:
                db.rollback()
                logging.exception(e)
        q.join()

def insert_upcoming_movies(movie_data, db,cursor):
    "insert upcoming new movies"
    new_movie_data = movie_compare(cursor, "upcoming_movies", movie_data["data"]["upcoming_movies"])
    if new_movie_data:
        for movie_detail in new_movie_data:
            try:
                db.execute("INSERT INTO upcoming_movies(title,link) VALUES(?,?)",
                       (movie_detail["title"],
                        "http://www.imdb.com/title/{}".format(movie_detail["imdb_code"]),))
                insert_movie_image(movie_detail["title"],
                                    movie_detail["medium_cover_image"], db)
                db.commit()
                announce('Upcoming Movie', movie_detail["title"],
                         "http://www.imdb.com/title/{}".format(movie_detail["imdb_code"]))
            except Exception as e:
                db.rollback()
                logging.exception(e)
    else:
        logging.debug("no new upcoming movies")

def insert_movie_image(movie_title, image_url, db):
    if fetch_image(image_url, movie_title):
        try:
            db.execute("INSERT INTO movie_images(title,path) VALUES(?,?)",
                   (movie_title, movie_title+".png",))
        except sqlite3.IntegrityError:
            logging.info('image record already exists in database')

def fetch_image(image_url, title,):
    "fetch image"
    if os.path.isfile(settings.IMAGE_PATH+title+".png"):
        logging.debug("file already exists")
        return True
    else:
        try:
            with open(settings.IMAGE_PATH+title+".png",'wb') as image_file:
                image_file.write(urlopen(image_url).read())
                logging.debug("imaged fetched")
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
        if movie_data["title"]  not in old_movie_data:
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
