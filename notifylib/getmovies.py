from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from notifylib.notify import announce
import logging
import re


class Get_Movies:
    def __init__(self, cursor, connect):
        self.cursor = cursor
        self.connect = connect

    def fetch_new_movies(self):
        request = Request("http://www.primewire.ag/index.php?sort=featured",
                  headers = {'User-Agent': 'Mozilla/5.0'})
        featured_movies = urlopen(request).read().decode('UTF-8')
        soup = BeautifulSoup(featured_movies)
        div_class = soup.find_all('div',{'class':'index_item index_item_ie'})
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
            except Exception as e:
                pass
            try:
                self.cursor.execute("SELECT Id from genre where genre=?",
                                    (temp_list[1][0],))
                key = self.cursor.fetchone()
                new_data.append((int(key[0]), temp_list[0][0], temp_list[0][1]))
            except Exception as e:
                logging.warn("Unable to fill new_data list")
                logging.exception(e)
        return new_data

    def insert_new_movies(self, new_movie_list):
        diff_movie = compare(self.cursor, new_movie_list)
        try:
                for movie_data in diff_movie:
                        self.cursor.execute("INSERT INTO movies(genre_id,title,link) VALUES(?,?,?)",
                                     (movie_data[0], movie_data[1], movie_data[2]),)
                        self.connect.commit()
                        announce('New Movie',movie_data[1],
                                 "http://www.primewire.ag"+movie_data[2])
        except Exception as e:
                logging.error("Unable to insert movie")
                logging.exception(e)
                self.connect.rollback()


def compare(cursor, new_list):
    old_list = []
    cursor.execute('SELECT genre_id,title,link from movies')
    data = cursor.fetchall()
    for old_data in data:
        old_list.append((old_data[0], old_data[1], old_data[2]))
    diff_movies = set(new_list).difference(old_list)
    return diff_movies

def fetch_movie_image(page):
    #fetch the image from here and insert into image db
