import requests
import logging
import re
import sqlite3
import concurrent.futures as cf
import os

from bs4 import BeautifulSoup as Soup
from datetime import datetime as dt

from . import settings

PRIMEWIRE_FEATURED_MOVIES_URL = 'http://www.primewire.ag/index.php?sort=featured'

def get_new_movies():
    "check for new movies"
    logging.debug("checking for new movies")
    page = featured_movies()
    if page:
        logging.debug("got featured movies html page")
        find_movies(page)


def featured_movies():
    "fetch primewire featured movies html page"
    try:
        req = requests.get(PRIMEWIRE_FEATURED_MOVIES_URL,
                               headers={'User-Agent': 'Mozilla/5.0'})
        return req.text
    except ConnectionError:
        logging.error("unable to fetch new featured movies")
        return None

def find_movies(html_page):
    "find movies from html page"
    page = Soup(html_page, 'lxml')
    movies = page.find_all('div',
                               {'class':'index_item index_item_ie'})
    for movie in movies:
        title = movie.a['title']
        date = re.search(r'\d{4}', title).group(0)
        movie_link = movie.a['href']
        movie_image_url = movie.a.img['src']
        try:
            logging.debug('got movie {}, fetching its image'.format(title[6:][:-7]))
            image_name = title[6:][:-7]+'.{}'.format(movie_image_url[-3:])
            image_file_path = os.path.join(settings.MOVIE_IMAGE_DIRECTORY, image_name)
            if not os.path.isfile(image_file_path):
                poster(movie_image_url, image_file_path)
                movie_insert(title[6:][:-7], date, movie_link,
                                 image_file_path)
        except ConnectionError:
            logging.error('unable to fetch details for movie {}'.format(title))


def poster(image_link, image_file_path):
    "download movie poster and return file path"
    try:
        image_response = requests.get('http:'+image_link,
                                          headers={'User-Agent': 'Mozilla/5.0'})
        if image_response.status_code == 200:
            logging.info('got image, writing to file')
            with open(image_file_path, 'wb') as image:
                    image.write(image_response.content)
                    logging.debug('image written to file')
                    return image_file_path
        else:
            logging.warn("Unable to connect to images.primewire.ag")
            raise
    except ConnectionError:
        raise
        

def movie_insert(title, date, movie_link, image_path):
    "insert new movie into database"
    conn = sqlite3.connect(settings.MOVIE_DB_PATH,
                               detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('pragma foreign_keys=on')
    c = conn.cursor()
    try:
        row_id = c.execute("INSERT INTO movie(title, year, url, date_added) VALUES(?,?,?,?)",
                      (title, date, movie_link, dt.now()))
        c.execute("INSERT into image(movie_id, path) VALUES(?,?)",
                      (row_id.lastrowid, image_path))
        c.execute('INSERT INTO detail_queue(movie_id) VALUES(?)',
                      (row_id.lastrowid,))
        conn.commit()
        logging.debug("{} inserted into database")
    except sqlite3.IntegrityError:
        logging.warn('movie {} already exists'.format(title))
    except sqlite3.OperationalError as e:
        logging.error('unable to insert new movie {}'.format(title))
        logging.error(e)
    finally:
        conn.close()
