from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from notifylib.notify import announce
from datetime import datetime
from notifylib import settings
import logging
import re
import sqlite3


class Get_Movies:
    def __init__(self, cursor, connect):
        self.cursor = cursor
        self.connect = connect

    def fetch_new_movies(self):
        "Get all movies from page"
        request = Request("http://www.primewire.ag/index.php?sort=featured",
                  headers={'User-Agent': 'Mozilla/5.0'})
        featured_movies = urlopen(request).read().decode('UTF-8')
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
        jpg_links = process_page(movie_page)
        diff_movie = compare(self.cursor, new_movie_list)
        try:
            for movie_data in diff_movie:
                self.cursor.execute("INSERT INTO movies(genre_id,title,link,date_added) VALUES(?,?,?,?)",
                                     (movie_data[0], movie_data[1], movie_data[2],datetime.now(),))
                self.connect.commit()
                announce('New Movie', movie_data[1],"http://www.primewire.ag"+movie_data[2])
                get_movie_poster(jpg_links, movie_data[1], movie_data[2],
                                 self.cursor, self.connect)
        except sqlite3.IntegrityError as e:
            logging.error("Unable to insert movie")
            logging.exception(e)
            self.connect.rollback()


def process_page(movie_page):
    "find image links from page"
    jpg_posters = []
    for image_jpg in movie_page:
        jpg_posters.append(image_jpg.find('img')['src'])
    return jpg_posters


def get_movie_poster(jpg_links, movie_title, movie_link, cursor, connect):
    "Get images"
    number = re.search(r'\d{4,}', movie_link)
    for url_link in jpg_links:
        if re.search(number.group(0), url_link):
            with open("%s" %(settings.IMAGE_PATH+movie_title+".jpg"),'wb') as image_file:
                image_request = Request(url_link,
                                        headers={'User-Agent': 'Mozilla/5.0'})
                image_file.write(urlopen(image_request).read())
                logging.info("Image fetched")
                cursor.execute("SELECT id FROM movies WHERE title=?",
                               (movie_title,))
                key = cursor.fetchone()
                cursor.execute("INSERT INTO movie_images(movie_id,path) VALUES(?,?)",
                               (key[0], settings.IMAGE_PATH+movie_title+".jpg",))
                cursor.execute("UPDATE config set value=? where key='last_movie_id'",
                               (key[0],))
                connect.commit()

def compare(cursor, new_list):
    "Compare new move_list with old movie List"
    old_list = []
    cursor.execute('SELECT genre_id,title,link from movies')
    data = cursor.fetchall()
    for old_data in data:
        old_list.append((old_data[0], old_data[1], old_data[2]))
    diff_movies = set(new_list).difference(old_list)
    return diff_movies
