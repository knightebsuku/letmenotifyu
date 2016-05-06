import sqlite3
import logging
import requests
from aiohttp import ClientSession


from . import settings
from bs4 import BeautifulSoup as Soup

logger = logging.getLogger(__name__)

PRIMEWIRE_URL = 'http://www.primewire.ag'
OMDB_API_URL = 'http://www.omdbapi.com/?i=' #tt0372784


class MovieDetail:
    def __init__(self):
        self.connect = sqlite3.connect(settings.MOVIE_DB_PATH)
        self.cursor = self.connect.cursor()

    def _poll_queue(self):
        "Get all movies in queue"
        try:
            self.cursor.execute("SELECT movie.id,url FROM movie JOIN detail_queue ON movie.id=movie_id WHERE detail_queue_status_id <> 2 limit 1")
            return self.cursor.fetchall()
        except sqlite3.OperationalError as e:
            logger.error("Unable to fetch movies in detail_queue")
            logger.error(e)

    def fetch(self):
        urls = self._poll_queue()
        if urls:
            for movie_id, movie_url in urls:
                html_page = self._fetch_page(movie_url)
                if html_page:
                    self._detail(movie_id, html_page)

    def _fetch_page(self, url):
        "Fetch movie detail html page"
        try:
            req = requests.get(PRIMEWIRE_URL+url)
            if req.status_code == 200:
                return req.text
        except requests.exceptions.ConnectionError():
            logger.error("Unable to fetch url for {}".format(PRIMEWIRE_URL+url))
                         
    def _detail(self, movie_id, web_page_text):
        "extract imdb url and insert into database"
        page = Soup(web_page_text, 'lxml')
        imdb_info = page.find('div', {'class': 'mlink_imdb'})
        if imdb_info:
            imdb_key = imdb_info.a['href'].strip('http://www.imdb.com/title/')
            try:
                details = self._omdbapi(imdb_key)
                self.cursor.execute("INSERT INTO detail(movie_id, imdb_key, 'released_date, plot, imdb_rating) VALUES(?,?,?,?,?)",
                                    (movie_id,
                                     imdb_key,
                                     details['Released'],
                                     details['Plot'],
                                     details['imdbRating']))
                actors = details['Actors'].split(',')
                self._actors(actors, movie_id)
            except sqlite3.OperationalError as e:
                logger.error("unable to insert imdb key for {}".format(movie_id))
                logger.error(e)

    def _omdbapi(self, imdb_key, movie_id):
        "Get full movie details"
        req = requests.get(OMDB_API_URL+imdb_key)
        if req.headers['content-type'] == 'application/json; charset=utf-8':
            data = req.json()
            if data['Response'] == True:
                return data

    def _actors(self, actors, movie_id):
        "insert movie actors"
        for actor in actors:
            try:
                self.cursor.execute('INSERT INTO actor(name) VALUES(?)',
                                    (actor,))
                actor_id = self.cursor.lastrowid()
            except sqlite3.IntegrityError:
                logger.warn("actor {} already exists".format(actor))
                self.cursor.execute("SELECT id FROM actor WHERE name=?",(actor))
                self.cursor.execute("INSERT INTO movie_actors(movie_id, actor_id) VALUES(?,?)", (movie_id, self.cursor.fetchone[0]))
            else:
                self.cursor.execute('INSERT INTO movie_actors(movie_id, actor) VALUES(?,?)', (movie_id, actor_id))
