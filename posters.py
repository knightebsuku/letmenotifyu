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
    with open("%s" % (IMAGE_PATH+link[1]+".jpg"), 'wb') as image_file:
        image_request = Request(meta['content'],
                          headers={'User-Agent': 'Mozilla/5.0'})
        image_file.write(urlopen(image_request).read())
        print("Imaged fetched")
        try:
            cursor.execute("INSERT INTO movie_images(movie_id,path) VALUES(?,?)",
                                (link[0], IMAGE_PATH+link[1]+'.jpg',))
            connect.commit()
            cursor.execute("UPDATE config set value=? where key='last_movie_id'",(link[0],))
            connect.commit()
        except sqlite3.IntegrityError:
            print("File already exists")
            pass


def get_posters():
    print("connecting to database")
    connect = sqlite3.connect(os.environ['HOME']+'/.local/share/letmenotifyu/dev.sqlite')
    cursor = connect.cursor()
    cursor.execute("SELECT id,title,link from movies where id >"+
                   '(SELECT cast(value as INTEGER) from config where key="last_movie_id")')
    for link in cursor.fetchall():
        print("getting page of:", link[1])
        request = Request('http://www.primewire.ag'+link[2],
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


