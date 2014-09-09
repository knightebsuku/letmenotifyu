#!/usr/bin/python3

import sqlite3
import os
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

IMAGE_PATH = os.environ['HOME']+'/.local/share/letmenotifyu/images/'


def correct_decode(code, request, link, cursor, connect):
        soup = BeautifulSoup(urlopen(request).read().decode(code))
        meta = soup.find('meta', {'property': 'og:image'})
        print("fetching image", meta['content'])
        with open("%s" % (IMAGE_PATH+link[0]+".jpg"), 'wb') as image_file:
                image_file.write(urlopen(meta['content']).read())
                print("Imaged fetched")
                cursor.execute("SELECT id FROM movies WHERE title=?", (link[0],))
                key = cursor.fetchone()
                try:
                        cursor.execute("INSERT INTO movie_images(movie_id,path) VALUES(?,?)",
                                (key[0], IMAGE_PATH+link[0]+'.jpg',))
                        connect.commit()
                except sqlite3.IntegrityError:
                        print("File already exists")
                        pass


def get_posters():
    print("connecting to database")
    connect = sqlite3.connect(os.environ['HOME']+'/.local/share/letmenotifyu/dev.sqlite')
    cursor = connect.cursor()
    cursor.execute("SELECT title,link from movies")
    for link in cursor.fetchall():
        print("getting page of:", link[0])
        request = Request('http://www.primewire.ag'+link[1],
                          headers={'User-Agent': 'Mozilla/5.0'})
        try:
                correct_decode("UTF-8", request, link, cursor, connect)
        except UnicodeDecodeError:
                print("Page is not in UTF-8, trying latin-1.....")
                correct_decode("latin-1", request, link, cursor, connect)
                pass
        except TypeError:
                pass

get_posters()


