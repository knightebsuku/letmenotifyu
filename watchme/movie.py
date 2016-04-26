import logging
import re
import sqlite3
import os

from bs4 import BeautifulSoup as Soup
from datetime import datetime as dt

from . import settings
from . import primewire

def new_movies():
    "check for new movies"
    logging.debug("checking for new movies")
    page = primewire.featured_movies_page()
    if page:
        logging.debug("got featured movies html page")
        find_movies(page)


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
        if all((title, date, movie_link, movie_image_url)):
            logging.debug('got movie {}, fetching its image'.format(title[6:][:-7]))
            image_name = title[6:][:-7]+'.{}'.format(movie_image_url[-3:])
            image_file_path = os.path.join(settings.MOVIE_IMAGE_DIRECTORY, image_name)
            if not os.path.isfile(image_file_path):
                if primewire.poster(movie_image_url, image_file_path):
                    movie_insert(title[6:][:-7], date, movie_link,
                                 image_file_path)

def movie_insert(title, date, movie_link, image_path):
    "insert new movie into database"
    conn = sqlite3.connect(settings.MOVIE_DB_PATH,
                               detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=on')
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
