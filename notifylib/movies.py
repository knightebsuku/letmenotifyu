from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from notifylib.notify import announce
from datetime import datetime
from notifylib import util
import logging
import re
import sqlite3
import urllib


class Movies:
    def __init__(self, cursor, connect):
        self.cursor = cursor
        self.connect = connect

    def fetch_new_movies(self):
        "Get all movies from page"
        request = Request("http://www.primewire.ag/index.php?sort=featured",
                  headers={'User-Agent': 'Mozilla/5.0'})
        try:
            featured_movies = urlopen(request).read().decode('UTF-8')
        except UnicodeDecodeError:
            featured_movies = urlopen(request).read().decode('latin1')
        except urllib.error.URLError:
            return
        soup = BeautifulSoup(featured_movies)
        div_class = soup.find_all('div', {'class': 'index_item index_item_ie'})
        new_data = []
        for links in div_class:
            temp_list = []
            for movie_links in links.find_all('a', {'href': re.compile("(/watch|/?genre)")}):
                title = movie_links.get_text()
                movie_title = title.replace("Watch", "")
                links = movie_links['href']
                temp_list.append([movie_title, links])
            try:
                self.cursor.execute("INSERT INTO genre(genre) VALUES(?)",
                                    (temp_list[1][0],))
                self.connect.commit()
            except sqlite3.IntegrityError as e:
                pass
            self.cursor.execute("SELECT Id from genre where genre=?",
                                    (temp_list[1][0],))
            key = self.cursor.fetchone()
            new_data.append((int(key[0]), temp_list[0][0], temp_list[0][1]))
        return new_data, div_class

    def insert_new_movies(self, new_movie_list, movie_page):
        "Insert new movies"
        poster_links = util.process_page(movie_page)
        diff_movie = util.movie_compare(self.cursor, new_movie_list)
        try:
            for movie_data in diff_movie:
                self.cursor.execute("INSERT INTO movies(genre_id,title,link,date_added) VALUES(?,?,?,?)",
                                     (movie_data[0], movie_data[1], movie_data[2],datetime.now(),))
                util.movie_poster(poster_links, movie_data[1], movie_data[2],
                                  self.cursor, self.connect)
                self.connect.commit()
                announce('New Movie', movie_data[1],"http://www.primewire.ag"+movie_data[2])
        except sqlite3.IntegrityError:
            logging.error("Movie Already exsists")
            self.connect.rollback()
