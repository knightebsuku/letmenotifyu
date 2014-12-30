from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from notifylib.notify import announce
from datetime import datetime
from notifylib import util
from notifylib import settings
import logging
import re
import sqlite3
import urllib
import json
import os
import hashlib

def get_upcoming_movies():
    "Get list of upcoming movies by yifi"
    try:
        yifi_url = urlopen("https://yts.re/api/upcoming.json")
        json_data = json.loads(yifi_url.read().decode('utf-8'))
        return json_data
    except Exception as e:
        logging.error("Unable to connect to the website")
        logging.exception(e)

def get_released_movies():
    "Get list of movies released by yifi"
    try:
        yifi_url = urlopen("https://yts.re/api/list.json?quality=720p&limit=50")
        json_data = json.loads(yifi_url.read().decode('utf-8'))
        return json_data
    except Exception as e:
        logging.error("unable to fetch movie list")
        logging.exception(e)

def insert_released_movies(data, cursor, db):
    "insert new movies"
    released_data = movie_compare(cursor, "movies", data["MovieList"])
    if released_data:
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
                announce('Newly Released Movie', movie_detail["MovieTitle"],
                         movie_detail["ImdbLink"])
                db.commit()
            except Exception as e:
                db.rollback()
                logging.exception(e)
                exit()

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
                announce('Upcoming Movie', movie_detail["MovieTitle"],
                         movie_detail["ImdbLink"])
                db.commit()
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

def fetch_torrent(torrent_url, movie_title, cursor):
    "fetch torrent images"
    if os.path.isfile(settings.TORRENT_DIRECTORY+movie_title+".torrent"):
        logging.debug("torrent file already exists")
    else:
        try:
            with open(settings.TORRENT_DIRECTORY+movie_title+".torrent","wb") as torrent_file:
                torrent_file.write(urlopen(torrent_url).read())
                logging.debug("torrent file downloded")
                correct = check_hash(settings.TORRENT_DIRECTORY+movie_title+".torrent",
                                     movie_title, cursor)
                if correct:
                    return True
        except Exception as e:
            logging.exception(e)
            return False
                


def check_hash(torrent_file, movie_title, cursor):
    "calculate hash_sum and check if it matches"
    cursor.execute("SELECT hash_sum from movies where title=?",(movie_title,))
    hash_sum = cursor.fetchone()[0]
    torrent_hash = hashlib.md5(open(torrent_file).read()).hexdigest()
    if torrent_hash == hash_sum:
        logging.debug("hash sums match")
        return True
    else:
        logging.debug("hash sum mismatch")
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
