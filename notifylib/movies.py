from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from notifylib.notify import announce
from datetime import datetime
from notifylib import util
from notifylib import settings
import logging
import re
import sqlite3
import urllib
import json

def get_upcoming_movies():
    "Get list of upcoming movies by yifi"
    try:
        yifi_url = urlopen("https://yts.re/api/upcoming.json")
        json_data = json.loads(yifi_url.read().decode('utf-8'))
        return json_data
    except Exception as e:
        logging.error("Unable to connect to the website")
        logging.exception(e)

def get_released_movies():
    "Get list of movies released by yifi"
    try:
        yifi_url = urlopen("https://yts.re/api/list.json?quality=720p&limit=50")
        json_data = json.loads(yifi_url.read().decode('utf-8'))
        return json_data
    except Exception as e:
        logging.error("unable to fetch movie list")
        logging.exception(e)

def insert_released_movies():
    "insert new movies"

def insert_upcoming_movies(movie_data, db,cursor):
    new_movie_data = movie_compare(cursor, "upcoming_movies", movie_data)
    if new_movie_data:
        for movie_detail in new_movie_data:
            try:
                db.execute("INSERT INTO upcoming_movies(title,link) VALUES(?,?)",
                       (movie_detail["MovieTitle"], movie_detail["ImdbLink"],))
                upcoming_movie_image(movie_detail["MovieTitle"],
                                    movie_detail["MovieCover"], db, cursor)
                announce('Upcoming Movie', movie_detail["MovieTitle"],
                         movie_detail["ImdbLink"])
            except Exception as e:
                db.rollback()
                logging.exception(e)
    else:
        logging.debug("no new upcoming movies")

def upcoming_movie_image(movie_title, image_url, db, cursor):
    cursor.execute("SELECT id FROM upcoming_movies WHERE title=?",
                   (movie_title,))
    title_id = cursor.fetchone()
    if fetch_image(image_url, movie_title):
        db.execute("INSERT INTO upcoming_images(movie_id,path) VALUES(?,?)",
                   (title_id[0], movie_title+".png",))
        db.commit()

def fetch_image(image_url, title,):
    "fetch image"
    try:
        with open(settings.IMAGE_PATH+title+".png",'wb') as image_file:
            image_file.write(urlopen(image_url).read())
            logging.debug("imaged fetched")
        return True
    except Exception as e:
        logging.exception(e)
        exit()
        return False

def movie_compare(cursor, table, new_data):
    "compare new movie list to current database"
    new_movie_data = []
    cursor.execute("SELECT title from "+table)
    data = [x[0] for x in cursor.fetchall()]
    logging.debug(data)
    for movie_data in new_data:
        if movie_data["MovieTitle"]  not in data:
            new_movie_data.append(movie_data)
    return new_movie_data

## class Movies:
##     def __init__(self, cursor, connect):
##         self.cursor = cursor
##         self.connect = connect

##     def fetch_new_movies(self):
##         "Get all movies from page"
##         request = Request("http://www.primewire.ag/index.php?sort=featured",
##                   headers={'User-Agent': 'Mozilla/5.0'})
##         try:
##             featured_movies = urlopen(request).read().decode('UTF-8')
##         except UnicodeDecodeError:
##             featured_movies = urlopen(request).read().decode('latin1')
##         except urllib.error.URLError:
##             return
##         soup = BeautifulSoup(featured_movies)
##         div_class = soup.find_all('div', {'class': 'index_item index_item_ie'})
##         new_data = []
##         for links in div_class:
##             temp_list = []
            ## for movie_links in links.find_all('a', {'href': re.compile("(/watch|/?genre)")}):
            ##     title = movie_links.get_text()
            ##     movie_title = title.replace("Watch", "")
            ##     links = movie_links['href']
            ##     temp_list.append([movie_title, links])
            ## try:
            ##     self.cursor.execute("INSERT INTO genre(genre) VALUES(?)",
            ##                         (temp_list[1][0],))
            ##     self.connect.commit()
            ## except sqlite3.IntegrityError as e:
    ##             pass
    ##         self.cursor.execute("SELECT Id from genre where genre=?",
    ##                                 (temp_list[1][0],))
    ##         key = self.cursor.fetchone()
    ##         new_data.append((int(key[0]), temp_list[0][0], temp_list[0][1]))
    ##     return new_data, div_class

    ## def insert_new_movies(self, new_movie_list, movie_page):
    ##     "Insert new movies"
    ##     poster_links = util.process_page(movie_page)
    ##     diff_movie = util.movie_compare(self.cursor, new_movie_list)
    ##     try:
    ##         for movie_data in diff_movie:
    ##             self.cursor.execute("INSERT INTO movies(genre_id,title,link,date_added) VALUES(?,?,?,?)",
    ##                                  (movie_data[0], movie_data[1], movie_data[2],datetime.now(),))
    ##             util.movie_poster(poster_links, movie_data[1], movie_data[2],
    ##                               self.cursor, self.connect)
    ##             self.connect.commit()
    ##             announce('New Movie', movie_data[1],"http://www.primewire.ag"+movie_data[2])
    ##     except sqlite3.IntegrityError:
    ##         logging.error("Movie Already exsists")
    ##         self.connect.rollback()
