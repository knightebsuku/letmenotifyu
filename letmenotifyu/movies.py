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
        yifi_url = urlopen("https://yts.re/api/upcoming.json")
        json_data = json.loads(yifi_url.read().decode('utf-8'))
        return json_data
    except Exception:
        logging.error("Unable to connect to the website")

def get_released_movies(cursor):
    "Get list of movies released by yifi"
    try:
        quality = util.get_config_value(cursor,"movie_quality")
        limit = util.get_config_value(cursor,'max_movie_results')
        yifi_url = urlopen("https://yts.re/api/list.json?quality={}&limit={}".format(quality,limit))
        json_data = json.loads(yifi_url.read().decode('utf-8'))
        return json_data
    except Exception as e:
        logging.error("unable to fetch movie list")
        logging.exception(e)

def get_movie_details(yify_id):
    try:
        yify_url = urlopen("https://yts.re/api/movie.json?id={}".format(yify_id))
        movie_detail = json.loads(yify_url.read().decode('utf-8'))
        return movie_detail
    except (urllib.error.URLError,urllib.error.HTTPError):
        logging.warn("Unable to download movie detail")

def insert_movie_details(q):
    connect = sqlite3.connect(settings.DATABASE_PATH)
    cursor = connect.cursor()
    while True:
        [movie_id,yify_id] = q.get()
        movie_detail = get_movie_details(yify_id)
        if 'status' in movie_detail.keys():
            logging.warn("No data for current movie")
            q.task_done()
        elif not movie_detail:
            logging.warn("Cant connect to movie_detail")
            q.task_done()
        else:
            try:
                connect.execute("INSERT INTO movie_details(movie_id,language,movie_rating,"+
                                    'youtube_url,description) '+
                                    'VALUES(?,?,?,?,?)',(movie_id,movie_detail['Language'],
                                                         movie_detail['MovieRating'],
                                                         movie_detail["YoutubeTrailerUrl"],
                                                         movie_detail["LongDescription"],))
                for actor in movie_detail["CastList"]:
                    try:
                        row = connect.execute("INSERT INTO actors(name,actor_link) "+
                                          'VALUES(?,?)',(actor["ActorName"], actor['ActorImdbLink'],))
                        connect.execute("INSERT INTO actors_movies(actor_id,movie_id) "+
                                    'VALUES(?,?)',(row.lastrowid, movie_id,))
                        connect.commit()
                    except sqlite3.IntegrityError:
                        logging.error("record already exsists")
                        cursor.execute("SELECT id from actors where name=?", (actor["ActorName"],))
                        (actor_id,) = cursor.fetchone()
                        connect.execute("INSERT INTO actors_movies(actor_id,movie_id) "+
                                        'VALUES(?,?)', (actor_id,movie_id,))
                        logging.info("Movie Detail complete")
                    except sqlite3.OperationalError as e:
                        logging.exception(e)
                    finally:
                        connect.commit()
            except sqlite3.IntegrityError:
                logging.warn("Movie Detail already exists")
            except sqlite3.OperationalError as e:
                logging.exception(e)
            finally:
                q.task_done()

def insert_released_movies(data, cursor, db):
    "insert new movies"
    released_data = movie_compare(cursor, "movies", data["MovieList"])
    if released_data:
        q = Queue(maxsize=0)
        details_worker = Thread(target=insert_movie_details, args=(q,))
        details_worker.setDaemon(True)
        details_worker.start()
        for movie_detail in released_data:
            try:
                genre_id = get_movie_genre(movie_detail["Genre"], cursor, db)
                row = db.execute("INSERT INTO movies(genre_id,title,link,date_added,movie_id)"+
                           'VALUES(?,?,?,?,?)',
                           (genre_id,
                            movie_detail['MovieTitle'],
                            movie_detail["ImdbLink"],
                            movie_detail["DateUploaded"],
                            movie_detail["MovieID"],))
                db.execute("INSERT INTO movie_torrent_links(movie_id,link,hash_sum) VALUES(?,?,?)",
                           (row.lastrowid, movie_detail["TorrentUrl"], movie_detail["TorrentHash"],))
                insert_movie_image(movie_detail["MovieTitle"], movie_detail["CoverImage"], db)
                q.put([row.lastrowid, movie_detail["MovieID"]])
                #db.execute("DELETE FROM upcoming_movies where title=?",(movie_detail['MovieTitle'],))
                db.commit()
                announce('Newly Released Movie', movie_detail["MovieTitle"],
                         movie_detail["ImdbLink"])
            except Exception as e:
                db.rollback()
                logging.exception(e)
        q.join()

def insert_upcoming_movies(movie_data, db,cursor):
    "insert upcoming new movies"
    new_movie_data = movie_compare(cursor, "upcoming_movies", movie_data)
    if new_movie_data:
        for movie_detail in new_movie_data:
            try:
                db.execute("INSERT INTO upcoming_movies(title,link) VALUES(?,?)",
                       (movie_detail["MovieTitle"], movie_detail["ImdbLink"],))
                insert_movie_image(movie_detail["MovieTitle"],
                                    movie_detail["MovieCover"], db)
                db.commit()
                announce('Upcoming Movie', movie_detail["MovieTitle"],
                         movie_detail["ImdbLink"])
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
    data = [x[0] for x in cursor.fetchall()]
    for movie_data in new_data:
        if movie_data["MovieTitle"]  not in data:
            new_movie_data.append(movie_data)
    return new_movie_data

def get_movie_genre(genre, cursor, db):
    cursor.execute("SELECT Id FROM genre where genre=?",(genre,))
    if cursor.fetchone() is None:
        logging.debug("genre does not exist yet")
        row = db.execute("INSERT INTO genre(genre) VALUES(?)",(genre,))
        genre_id = row.lastrowid
        return genre_id
    else:
        logging.debug('genre exists')
        cursor.execute("SELECT Id FROM genre where genre=?",(genre,))
        genre_id = cursor.fetchone()
        return int(genre_id[0])
