import sqlite3
import requests

from . import settings
from bs4 import BeautifulSoup as Soup
from queue import Queue

def fetch_movie_detail():
    urls = poll_detail_queue()
    for url, in urls:
        print(url)
        #detail(url)


def poll_detail_queue():
    "get movie details by polling detail queue table"
    conn = sqlite3.connect(settings.MOVIE_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT url FROM movie JOIN detail_queue ON movie.id=movie_id WHERE detail_queue_status_id <> 2")
    return c.fetchall()

def detail(url):
    pass
