#!/usr/bin/python3

import logging
import psycopg2
import os
import requests
import sqlite3

from urllib.request import urlretrieve
from letmenotifyu.notify import announce
from . import settings
from . import settings, yify
from datetime import datetime


log = logging.getLogger(__name__)


class Movie:
    connect = sqlite3.connect(settings.MOVIE_DB)
    cur = connect.cursor()
    new_movie_json = ''
    
    def __init__(self):
        pass
    def update(self):
        """
        Check for new movie updates
        """
        try:
            self.new_movie_json = yify.get_released_movies(self.cursor)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
            log.warn("Unable to connect to yify api")
            log.warn(e)
        else:
            if json_data['status'] == 'error':
                log.warn("yify api status error")
            else:
                for movie in self.compare():
                    log.info("fetch movie poster for {}".format(movie['title']))
                    if self._poster(movie['image'], movie['title']):
                        
                        
                    
                    
                
            
    
    def _poster(self, image_url, title):
        """
        Fetch new movie poster
        """
        if os.path.isfile(settings.IMAGE_PATH+title+".jpg"):
            log.debug("Image file for {} already downloaded".format(title))
            return True
        else:
            try:
                urlretrieve(image_url, settings.IMAGE_PATH+title+".jpg")
                logging.debug("imaged fetched for {}".format(title))
                return True
            except Exception as e:
                logging.exception(e)
                return False
        
        pass
    def _compare(self):
        """
        only return movies that are not already in the database
        """
        self.cur.execute("SELECT title FROM movies")
        current_movie_titles = [x[0] for x in self.cur.fetchall()]
        for movie in self.new_movie_json:
            if movie["title"] not in current_movie_titles:
                yield movie
                
    def _genre(self, genre):
        """
        create new genre or get new genre for new movie
        """
        self.cur.execute("SELECT id FROM genre WHERE genre=?", (genre,))
        if self.cur.fetchone() is None:
            log.debug("genre does not exist yet")
            self.cur.execute("INSERT INTO genre(genre) VALUES(?) RETURNING id", (genre,))
            genre_id = self.cur.fetchone()[0]
            return genre_id
        else:
            log.debug('genre exists')
            cursor.execute("SELECT id FROM genre WHERE genre=%s", (genre,))
            (genre_id,) = cursor.fetchone()
            return int(genre_id)
        pass

    def _poster_exists(self):
        """
        Check if movie poster exists
        """
        pass


def released_movies(data, cursor, db):
    """
    Get new movies from json file.
    Get movies posters as well.
    insert into database
    """
    if not data:
        log.info("Unable to get newly released movies")
    elif data["status"] == "error":
        log.info("api status error")
    else:
        for movie_detail in movie_compare(cursor, data['data']['movies']):
            log.debug("fetching image for {}".format(movie_detail['title']))
            if fetch_image(movie_detail["medium_cover_image"],
                           movie_detail['title']):
                try:
                    log.debug("getting movie genre")
                    genre_id = get_movie_genre(movie_detail["genres"][0],
                                               cursor, db)
                    cursor.execute("INSERT INTO movies("
                                   "genre_id,title,link,date_added,"
                                   "yify_id,year) "
                                   'VALUES(%s,%s,%s,%s,%s,%s) RETURNING id',
                                   (genre_id,
                                    movie_detail['title'],
                                    movie_detail["imdb_code"],
                                    datetime.now(),
                                    movie_detail["id"],
                                    movie_detail["year"],))
                    row_id = cursor.fetchone()[0]
                    cursor.execute("INSERT INTO movie_torrent_links("
                                   "movie_id,link,hash_sum) "
                                   "VALUES(%s,%s,%s)",
                                   (row_id,
                                    movie_detail["torrents"][0]["url"],
                                    movie_detail["torrents"][0]["hash"],))
                    if image_record_exists(movie_detail['title'], cursor):
                        pass
                    else:
                        cursor.execute("INSERT INTO movie_images(title,path)"
                                       " VALUES(%s,%s)",
                                       (movie_detail['title'],
                                        movie_detail['title']+".jpg",))
                    db.commit()
                    announce('Newly Released Movie',
                             "{} ({})".format(movie_detail["title"],
                                              movie_detail["genres"][0]),
                             "http://www.imdb.com/title/{}".format(
                                 movie_detail["imdb_code"]))
                except psycopg2.IntegrityError as e:
                    db.rollback()
                    logging.exception(e)
                except Exception as e:
                    db.rollback()
                    logging.exception(e)


def fetch_image(image_url, title,):
    "fetch image"
    if os.path.isfile(settings.IMAGE_PATH+title+".jpg"):
        log.debug("Image file for {} already downloaded".format(title))
        return True
    else:
        try:
            urlretrieve(image_url, settings.IMAGE_PATH+title+".jpg")
            logging.debug("imaged fetched for {}".format(title))
            return True
        except Exception as e:
            logging.exception(e)
            return False


def movie_compare(cursor, new_data):
    "compare new movie list to current database"
    cursor.execute("SELECT title FROM movies")
    old_movie_data = [x[0] for x in cursor.fetchall()]
    for movie_data in new_data:
        if movie_data["title"] not in old_movie_data:
            yield movie_data


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
