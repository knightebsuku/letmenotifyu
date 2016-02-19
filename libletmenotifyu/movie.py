import requests
import logging
import re
import sqlite3
import concurrent.futures as cf

from bs4 import BeautifulSoup as Soup
from queue import Queue
from datetime import datetime as dt

from . import settings

SAM_MOVIE_URL = 'https://kat.cr/user/SaM/uploads/'
JUGGS_MOVIE_URL = 'https://kat.cr/user/juggs/uploads/'
movie_queue = Queue()


def movie_info(movie):
    movie_header = movie.find('a', 'cellMainLink')
    if re.search("ETRG$",movie_header.text):
        movie_queue.put([movie_header.text, movie_header['href']])

def movie_page():
    "Get list of movies from the 1st page"
    try:
        req = requests.get(SAM_MOVIE_URL)
        html_page = Soup(req.text, 'lxml')
        torrent_uploaded = html_page.find_all('tr',{'class':['odd', 'even']})
        with cf.ThreadPoolExecutor() as executor:
            for torrent in executor.map(movie_info,
                                            torrent_uploaded):
                pass
        insert_movie()
            
    except Exception as e:
        logging.INFO(e)
        

def insert_movie():
    "insert movie from queue"
    while not movie_queue.empty():
        conn = sqlite3.connect(settings.MOVIE_DB_PATH)
        c = conn.cursor()
        title, url = movie_queue.get()
        try:
            c.execute("INSERT INTO movie(title, kickass_url, data_added) "\
                      "VALUES(?,?,?)", (title, url, dt.now()))
            c.execute("INSERT INTO movie_detail_queue(movie_id) "\
                          "VALUES(?)", (c.lastrowid,))
            conn.commit()
            logging.debug("Inserted {}".format(title))
            #moving to movie_detail_queue
        except sqlite3.IntegrityError:
            logging.warn("{} already exists".format(title))
