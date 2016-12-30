import logging
import os
import requests
import sqlite3

from .notify import announce
from . import settings
from datetime import datetime
from requests.exceptions import ConnectionError, HTTPError


log = logging.getLogger(__name__)


class Movie:
    def __init__(self, movie_json):
        self._movie = movie_json
        self._title = self._movie['title']
        self._id = self._movie['id']
        self._year = self._movie['year']
        self._genres = self._movie['genres']
        self._imdb = self._movie['imdb_code']
        self._poster_url = self._movie['medium_cover_image']
        self._torrent_url = self._movie['torrents'][0]['url']
        self._torrent_hash = self._movie['torrents'][0]['hash']
        self._image_file_path = os.path.join(settings.IMAGE_PATH,
                                             self._title + ".jpg")
        self.connect = sqlite3.connect(settings.MOVIE_DB)
        self.cur = self.connect.cursor()
        self.cur.execute(settings.SQLITE_WAL_MODE)

    def poster(self):
        """
        Fetch new movie poster
        """
        if os.path.isfile(self._image_file_path):
            log.debug("Image file for {} already downloaded".format(self._title))
            return True
        else:
            try:
                response = requests.get(self._poster_url)
                if response.status_code == 200:
                    with open(self._image_file_path, 'wb') as movie_poster:
                        movie_poster.write(response.content)
                        log.debug("imaged fetched for {}".format(self._title))
                        return True
            except (ConnectionError, HTTPError) as error:
                log.exception(error)
                return False

    def commit(self):
        genre_id = self._genre(self._genres)
        try:
            self.cur.execute("INSERT INTO movies("
                             "genre_id,title,link,date_added,"
                             "yify_id,year) "
                             'VALUES(?,?,?,?,?,?)',
                             (genre_id,
                              self._title,
                              self._imdb,
                              datetime.now(),
                              self._id,
                              self._year))
            new_id = self.cur.lastrowid
            self.cur.execute("INSERT INTO movie_torrent_links("
                             "movie_id,link,hash_sum) "
                             "VALUES(?,?,?)",
                             (new_id,
                              self._torrent_url,
                              self._torrent_hash,))
            self.cur.execute("INSERT INTO movie_images(movie_id, path)"
                             "VALUES(?,?)",
                             (new_id, self._image_file_path))
            self.connect.commit()
            announce('Newly Released Movie', "{}".format(self._title))
        except(sqlite3.ProgrammingError) as error:
            log.error("Unable to insert movie {}".format(self._title))
            log.exception(error)
            self.connect.rollback()
        except sqlite3.IntegrityError:
            log.warn("movie {} already exists".format(self._title))
            self.connect.rollback()
        finally:
            self.connect.close()

    def _genre(self, genre: str) -> int:
        """
        create new genre or get new genre for new movie
        """
        s = self._genres[0]
        self.cur.execute("SELECT id FROM genre WHERE genre=?", (s,))
        if self.cur.fetchone() is None:
            log.debug("creating new genre {}".format(s))
            self.cur.execute("INSERT INTO genre(genre)"
                             "VALUES(?)", (s,))
            return self.cur.lastrowid
        else:
            log.debug('genre {} already exists'.format(s))
            self.cur.execute("SELECT id FROM genre WHERE genre=?", (s,))
            (genre_id,) = self.cur.fetchone()
            return int(genre_id)
