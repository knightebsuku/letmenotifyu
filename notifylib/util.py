import webbrowser
import logging
import re
import sqlite3

from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from notifylib import settings


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
        webbrowser.open_new("http://www.primewire.ag"+link[0])
        logging.info("Opening link"+ link[0])
    else:
        webbrowser.open_new("http://www.primewire.ag"+link)

def primewire(episode_site):
    "process series page"
    try:
        req = Request(episode_site, headers={'User-Agent': 'Mozilla/5.0'})
        data = urlopen(req).read().decode('ISO-8859-1')
        soup = BeautifulSoup(data)
        episode_page_data = soup
        all_series_info = []
        div_class = episode_page_data.find_all('div', {'class':'tv_episode_item'})
        for links in div_class:
            for series_links in links.find_all('a'):
                all_series_info.append((series_links.get('href'),
                                        links.get_text().replace(" ", "").replace("\n",'')))
            seasons = episode_page_data.findAll("h2",
                                                    text=re.compile(r'^Season'))
        return all_series_info, len(all_series_info), len(seasons)
    except Exception as e:
        logging.warn("Unable to connect to %s " % episode_site)
        logging.exception(e)

def series_compare(cursor, new_list, series_id):
    "Compare db list with new series"
    old_list = []
    cursor.execute("SELECT episode_link,episode_name from episodes where id=?",
                   (series_id,))
    data = cursor.fetchall()
    for old_episode in data:
        old_list.append((old_episode[0],old_episode[1].replace("\n", "")))
    list_difference = set(new_list).difference(old_list)
    logging.info(list_difference)
    return list_difference

def series_poster(cursor, connect, series_id):
    "fetch series JPEG"
    cursor.execute("SELECT title,series_link from series where id=?", (series_id,))
    series_link = cursor.fetchone()
    correct_decode(series_link, cursor)
    try:
        cursor.execute("INSERT INTO series_images(series_id,path) VALUES(?,?)",
                            (series_id, settings.IMAGE_PATH+series_link[0]+'.jpg',))
        connect.commit()
    except sqlite3.IntegrityError:
        logging.warn("File already exists")
        pass


def correct_decode(info, cursor):
    "fetch and decode images"
    request = Request(info[1],
                      headers={'User-Agent': 'Mozilla/5.0'})
    try:
        soup = BeautifulSoup(urlopen(request).read().decode("UTF-8"))
    except UnicodeDecodeError:
        soup = BeautifulSoup(urlopen(request).read().decode("latin1"))
    finally:
        meta = soup.find('meta', {'property': 'og:image'})
        print("fetching image", meta['content'])
        with open("%s" % (settings.IMAGE_PATH+info[0]+".jpg"), 'wb') as image_file:
            image_request = Request(meta['content'],
                          headers={'User-Agent': 'Mozilla/5.0'})
            image_file.write(urlopen(image_request).read())
            print("Imaged fetched")

## def movies(cursor):
##     cursor.execute("SELECT id,title,link from movies where id >"+
##                    '(SELECT cast(value as INTEGER) from config where key="last_movie_id")')
##     for link in cursor.fetchall():
##         print("getting page of:", link[1])
##         request = Request('http://www.primewire.ag'+link[2],
##                           headers={'User-Agent': 'Mozilla/5.0'})
##         try:
##             correct_decode("UTF-8", request, link, cursor, connect)
##         
##             print("Page is not in UTF-8, trying latin-1.....")
##             correct_decode("latin-1", request, link, cursor, connect)
##             pass
##         except TypeError:
##             pass        
