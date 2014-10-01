import webbrowser
import logging

from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from notifylib import settings
import re

def open_page(cursor, link, option=""):
    "open webbrowser page"
    if option == "movie":
        cursor.execute("SELECT link FROM movies where title=?", (movie,))
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
        div_class = episode_page_data.find_all('div',{'class':'tv_episode_item'})
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
    old_list = []
    cursor.execute("SELECT episode_link,episode_name from episodes where id=?",
                   (series_id,))
    data = cursor.fetchall()
    for old_episode in data:
        old_list.append((old_episode[0],old_episode[1].replace("\n", "")))
    list_difference = set(new_list).difference(old_list)
    logging.info(list_difference)
    return list_difference

def series_poster(cursor, connect):
    cursor.execute("SELECT id,title,series_link FROM series where id >"+
               '(SELECT cast(value as INTEGER) from config where key="last_series_id")')
    for series_info in cursor.fetchall():
        correct_decode(series_info,cursor)
        try:
            cursor.execute("INSERT INTO series_images(series_id,path) VALUES(?,?)",
                            (series_info[0], settings.IMAGE_PATH+series_info[1]+'.jpg',))
            cursor.execute("UPDATE config set value=? where key='last_series_id'",
                       (series_info[0],))
            connect.commit()
        except sqlite3.IntegrityError:
            print("File already exists")
            pass


def correct_decode(info, cursor):
    request = Request(info[2],
                      headers={'User-Agent': 'Mozilla/5.0'})
    try:
        soup = BeautifulSoup(urlopen(request).read().decode("UTF-8"))
    except UnicodeDecodeError:
        soup = BeautifulSoup(urlopen(request).read().decode("latin1"))
    finally:
        meta = soup.find('meta', {'property': 'og:image'})
        print("fetching image", meta['content'])
        with open("%s" % (settings.IMAGE_PATH+info[1]+".jpg"), 'wb') as image_file:
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
