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
from datetime import datetime


def initialise():
    os.mkdir(settings.DIRECTORY_PATH)
    os.mkdir(settings.IMAGE_PATH)
    os.mkdir(settings.TORRENT_DIRECTORY)
    settings.create_ini_file()
    

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


def open_page(cursor, link, option=None):
    "open webbrowser page"
    if option == "movie":
        cursor.execute("SELECT link FROM movies where title=?", (link,))
        link = cursor.fetchone()
        webbrowser.open_new(link[0])
        logging.info("Opening link" + link[0])
    else:
        webbrowser.open_new("http://www.primewire.ag"+link)
        logging.info("Opening link" + link)


def primewire(episode_site):
    "process series page"
    try:
        req = Request(episode_site, headers={'User-Agent': 'Mozilla/5.0'})
        data = urlopen(req).read().decode('ISO-8859-1')
        series_page_data = BeautifulSoup(data)
        all_series_info = []
        for episode_item in series_page_data.find_all('div', {'class': 'tv_episode_item'}):
            link = episode_item.a['href']
            ep_no = episode_item.find('a').contents[0]
            ep_name = episode_item.find('a').contents[1].text
            all_series_info.append((link, ep_no.replace(" ", "")+ep_name))
            seasons = series_page_data.find_all('a', {'class': 'season-toggle'})
        return all_series_info, len(all_series_info), len(seasons)
    except urllib.error.URLError:
        logging.warn("Unable to connect to {} ".format(episode_site))

def series_poster(cursor, connect, series_id):
    "fetch series JPEG"
    cursor.execute("SELECT title,series_link from series where id=?", (series_id,))
    (title, series_link) = cursor.fetchone()
    try:
        correct_decode(title, series_link)
        cursor.execute("INSERT INTO series_images(series_id,path) VALUES(?,?)",
                            (series_id, '{}.jpg'.format(title),))
        connect.commit()
    except sqlite3.IntegrityError:
        logging.warn("File already exists")


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
        logging.warn("Unable to connect to image link")
    except TypeError:
        logging.info("Cant find image link")


def save_image(movie_link, meta):
    if os.path.isfile(settings.IMAGE_PATH+movie_link+".jpg"):
        logging.info("File already exists")
    else:
        logging.info("fetching image "+movie_link)
        with open("%s" % (settings.IMAGE_PATH+movie_link+".jpg"), 'wb') as image_file:
            full_image_url = "http:"+meta['content']
            image_request = Request(full_image_url,
                          headers={'User-Agent': 'Mozilla/5.0'})
            image_file.write(urlopen(image_request).read())
            logging.info("Imaged fetched")

def process_page(movie_page):
    "find image links from page"
    jpg_posters = []
    for image_jpg in movie_page:
        jpg_posters.append(image_jpg.find('img')['src'])
    return jpg_posters

def check_url(text, notice, dialog, cursor, connection, link_box):
    "check adding new series"
    if re.search(r'http://www.primewire.ag/(.*)-\d+\-(.*)', text):
        title = re.search(r"http://www.primewire.ag/(.*)-\d+\-(.*)", text)
        change_string = title.group(2)
        show_title = change_string.replace("-", " ")
        logging.info("Inserting new series {}".format(show_title))
        try:
            cursor.execute('INSERT INTO series(title,' +
                           'series_link,' +
                           'number_of_episodes,' +
                           'number_of_seasons,' +
                           'status,' +
                           'current_season,' +
                           'last_update)' +
                           ' VALUES(?,?,0,0,1,0,?)',
                           (show_title, text, datetime.now(),))
            connection.commit()
            logging.debug("Series Added: {}".format(show_title))
            link_box.set_text('')
            dialog.get_object('linkdialog').destroy()
        except sqlite3.IntegrityError:
            logging.error("Series already added")
            notice.set_text("Series already added")
            notice.set_visible(True)
            dialog.get_object('imcheck').set_visible(True)
    else:
        notice.set_text("Not a valid link or link already exists")
        notice.set_visible(True)
        dialog.get_object('imcheck').set_visible(True)
        logging.warn("Invalid link:"+text)


def which_sql_message(Instruction):
    if Instruction == "start":
        use_sql = "UPDATE series SET status=1 where title=?"
        message = "Are you sure you want to start updating"
    elif Instruction == "stop":
        use_sql = "UPDATE series SET status=0 where title=?"
        message = "Are you sure you want to stop updating"
    elif Instruction == "delete":
        use_sql = "DELETE FROM series WHERE title=?"
        message = "Are you sure you want to delete"
    return message, use_sql

def fetch_current_season(cursor, series_title):
    cursor.execute('SELECT current_season from series where title=?', (series_title,))
    (no_season) = cursor.fetchone()
    return str(no_season)


def start_logging():
    "Start logging"
    logging.basicConfig(filename=settings.LOG_FILE_PATH,
                            format='%(asctime)s - %(message)s', filemode='w',
                            level=logging.DEBUG)


def pre_populate_menu(builder):
    header_list = builder.get_object('HeaderList')
    header = header_list.append(None, ["Movies"])
    header_list.append(header, ["Upcoming Movies"])
    header_list.append(header, ["Released Movies"])
    header = header_list.append(None, ["Series"])
    header_list.append(header, ["Latest Episodes"])
    header_list.append(header, ["Active Series"])
    header_list.append(header, ["Series Archive"])
    header = header_list.append(None, ['Watch Queue'])
    header_list.append(header, ["Movie Queue"])
    header_list.append(header, ["Series Queue"])


def fetch_torrent(torrent_url, title):
    "fetch torrent images"
    if os.path.isfile(settings.TORRENT_DIRECTORY+title+".torrent"):
        logging.debug("torrent file already exists")
        return True
    else:
        try:
            r = requests.get(torrent_url)
            with open(settings.TORRENT_DIRECTORY+title+".torrent","wb") as torrent_file:
                torrent_file.write(r.content)
                logging.debug("torrent file downloded")
                return True
        except Exception as e:
            logging.error("unable to fetch torrent")
            logging.exception(e)
            return False

def get_config_value(cursor, key):
    cursor.execute("SELECT value FROM config WHERE key=?",(key,))
    (value,) = cursor.fetchone()
    return value
    
