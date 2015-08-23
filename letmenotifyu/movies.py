#!/usr/bin/python3

from urllib.request import urlretrieve
from letmenotifyu.notify import announce
from . import settings, yify
import logging
import psycopg2
import os


def movie(connect, cursor):
    released_movie_data = yify.get_released_movies(cursor)
    if released_movie_data:
        released_movies(released_movie_data, cursor, connect)


def released_movies(data, cursor, db):
    "insert new movies"
    if not data:
        return
    elif data["status"] == "error":
        return
    else:
        released_data = movie_compare(cursor, "movies", data["data"]["movies"])
        for movie_detail in released_data:
            if fetch_image(movie_detail["medium_cover_image"], movie_detail['title']):
                try:
                    genre_id = get_movie_genre(movie_detail["genres"][0], cursor, db)
                    cursor.execute("INSERT INTO movies(genre_id,title,link,date_added,yify_id,year) "\
                                 'VALUES(%s,%s,%s,%s,%s,%s) RETURNING id',
                           (genre_id,
                            movie_detail['title'],
                            movie_detail["imdb_code"],
                            movie_detail["date_uploaded"],
                            movie_detail["id"],
                           movie_detail["year"],))
                    row_id = cursor.fetchone()[0]
                    cursor.execute("INSERT INTO movie_torrent_links(movie_id,link,hash_sum) "\
                                   "VALUES(%s,%s,%s)",
                           (row_id, movie_detail["torrents"][0]["url"], movie_detail["torrents"][0]["hash"],))
                    if image_record_exists(movie_detail['title'], cursor):
                        pass
                    else:
                        cursor.execute("INSERT INTO movie_images(title,path) VALUES(%s,%s)",
                               (movie_detail['title'], movie_detail['title']+".jpg",))
                    cursor.execute("DELETE FROM upcoming_movies WHERE title IN "\
                                   "(SELECT title FROM movies)")
                    db.commit()
                    announce('Newly Released Movie', "{} ({})".format(movie_detail["title"],
                                                                      movie_detail["genres"][0]),
                             "http://www.imdb.com/title/{}".format(movie_detail["imdb_code"]))
                except psycopg2.IntegrityError as e:
                    db.rollback()
                    logging.exception(e)
                except Exception as e:
                    db.rollback()
                    logging.exception(e)


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
