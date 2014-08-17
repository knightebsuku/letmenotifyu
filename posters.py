#!/usr/bin/python3

import sqlite3
import os
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

def get_posters():
    print("connecting to database")
    connect = sqlite3.connect(os.environ['HOME']+'/.local/share/letmenotifyu/dev.sqlite')
    cursor = connect.cursor()
    cursor.execute("SELECT link from movies")
    for link in cursor.fetchall():
        print("getting page of:", link)
        request = Request('http://www.primewire.ag'+link[0],
                          headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(urlopen(request).read().decode('UTF-8'))
        meta = soup.find('meta',{'property': 'og:image'})
        with open("%s" %(settings.IMAGE_PATH+movie_title),'wb') as image_file:
                image_file.write(urlopen(links).read())
                logging.info("Image fetched")
                cursor.execute("SELECT id FROM movies WHERE title=?", (movie_title),)
                key  = cursor.fetcone()
                cursor.execute("INSERT INTO movie_images(movie_id,path) VALUES(?,?)",
                               (key, settings.IMAGE_PATH+movie_title),)
                connect.commit()

        
        print(meta['content'])
        break

get_posters()
