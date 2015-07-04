#!/usr/bin/python3

import webbrowser
import logging
import re
import sqlite3
import urllib
import os
import requests

from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from letmenotifyu import settings


def render_view(image, string, store_model, image_file="ui/movies.png"):
    "Render GtkIconView"
    image.set_from_file(image_file)
    pixbuf = image.get_pixbuf()
    store_model.append([pixbuf, string])


def get_selection(view, store_model):
    "Get selection of GtkIconView"
    tree_path = view.get_selected_items()
    iters = store_model.get_iter(tree_path)
    model = view.get_model()
    selection = model.get_value(iters, 1)
    return selection


def open_page(cursor, title, option=None):
    "open webbrowser page"
    if option == 'upcoming':
        cursor.execute("SELECT link FROM upcoming_movies WHERE title=%s", (title,))
        (link,) = cursor.fetchone()
        webbrowser.open_new('http://www.imdb.com/title/{}'.format(link))
    else:
        webbrowser.open_new("http://www.primewire.ag"+title)
    logging.info("Opening link {}".format(title))


def series_poster(cursor, connect, series_id):
    "fetch series JPEG"
    cursor.execute("SELECT title,series_link FROM series WHERE id=%s", (series_id,))
    (title, series_link) = cursor.fetchone()
    try:
        correct_decode(title, series_link)
        cursor.execute("INSERT INTO series_images(series_id,path) VALUES(%s,%s)",
                            (series_id, '{}.jpg'.format(title),))
        connect.commit()
    except sqlite3.IntegrityError:
        logging.warn("Image for {} already exists".format(title))


def correct_decode(title, series_link):
    "fetch and decode images"
    if re.search(r'^http', series_link):
        request = Request(series_link,
                      headers={'User-Agent': 'Mozilla/5.0'})
    try:
        soup = BeautifulSoup(urlopen(request).read().decode("UTF-8"))
        meta = soup.find('meta', {'property': 'og:image'})
        save_image(title, meta)
    except UnicodeDecodeError:
        soup = BeautifulSoup(urlopen(request).read().decode("latin1"))
        meta = soup.find('meta', {'property': 'og:image'})
        save_image(title, meta)
    except urllib.error.URLError:
        logging.info("Unable to connect to image url".format(title))
    except TypeError:
        logging.info("Cant find image link for {}".format(title))


def save_image(movie_link, meta):
    if os.path.isfile(settings.IMAGE_PATH+movie_link+".jpg"):
        pass
    else:
        logging.debug("fetching image {}".format(movie_link))
        with open("%s" % (settings.IMAGE_PATH+movie_link+".jpg"), 'wb') as image_file:
            full_image_url = "http:"+meta['content']
            image_request = Request(full_image_url,
                          headers={'User-Agent': 'Mozilla/5.0'})
            image_file.write(urlopen(image_request).read())
            logging.debug("Imaged fetched")


def start_logging():
    "Start logging"
    logging.basicConfig(filename=settings.LOG_FILE_PATH,
                            format='%(asctime)s - %(name)s-%(levelname)s:%(message)s', filemode='w',
                            level=settings.LOG_LEVEL)


def pre_populate_menu(builder):
    header_list = builder.get_object('HeaderList')
    header = header_list.append(None, ["Movies"])
    header_list.append(header, ["Upcoming Movies"])
    header_list.append(header, ["Released Movies"])
    header_list.append(header, ["Movie Archive"])
    header = header_list.append(None, ["Series"])
    header_list.append(header, ["Latest Episodes"])
    header_list.append(header, ["Series on Air"])
    header_list.append(header, ["Series Archive"])
    header = header_list.append(None, ['Watch Queue'])
    header_list.append(header, ["Movie Queue"])
    header_list.append(header, ["Series Queue"])


def fetch_torrent(torrent_url, title):
    "fetch torrent images"
    if os.path.isfile(settings.TORRENT_DIRECTORY+title+".torrent"):
        return True
    else:
        try:
            r = requests.get(torrent_url)
            if r.status_code == requests.codes.ok:
                with open(settings.TORRENT_DIRECTORY+title+".torrent","wb") as torrent_file:
                    torrent_file.write(r.content)
                    return True
            else:
                return False
        except Exception as e:
            logging.error("unable to fetch torrent for {}".format(title))
            logging.exception(e)
            return False


def get_config_value(cursor, key):
    cursor.execute("SELECT value FROM config WHERE key=%s", (key,))
    (value,) = cursor.fetchone()
    return value
