import webbrowser
import logging
import re
import sqlite3
import urllib
import os

from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from notifylib import settings
from datetime import datetime


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
    except Exception:
        logging.warn("Unable to connect to %s " % episode_site)


def series_compare(cursor, new_list, series_id):
    "Compare db list with new series"
    old_list = []
    cursor.execute("SELECT episode_link,episode_name from episodes where series_id=?",
                   (series_id,))
    data = cursor.fetchall()
    for old_episode in data:
        old_list.append((old_episode[0], old_episode[1].replace("\n", "")))
    list_difference = set(new_list).difference(old_list)
    logging.info(new_list)
    return list_difference


def series_poster(cursor, connect, series_id):
    "fetch series JPEG"
    cursor.execute("SELECT title,series_link from series where id=?", (series_id,))
    series_link = cursor.fetchone()
    try:
        correct_decode(series_link)
        cursor.execute("INSERT INTO series_images(series_id,path) VALUES(?,?)",
                            (series_id, settings.IMAGE_PATH+series_link[0]+'.jpg',))
        connect.commit()
    except sqlite3.IntegrityError:
        logging.warn("File already exists")
        pass


def correct_decode(info):
    "fetch and decode images"
    if re.search(r'^http', info[1]):
        request = Request(info[1],
                      headers={'User-Agent': 'Mozilla/5.0'})
        image_type = "series"
    else:
        request = Request("http://www.primewire.ag"+info[1],
                      headers={'User-Agent': 'Mozilla/5.0'})
        image_type = "movie"
    try:
        soup = BeautifulSoup(urlopen(request).read().decode("UTF-8"))
        meta = soup.find('meta', {'property': 'og:image'})
        save_image(info[0], meta, image_type)
    except UnicodeDecodeError:
        soup = BeautifulSoup(urlopen(request).read().decode("latin1"))
        meta = soup.find('meta', {'property': 'og:image'})
        save_image(info[0], meta,image_type)
    except urllib.error.URLError:
        logging.warn("Unable to connect to image link")
    except TypeError:
        logging.info("Cant find image link")


def save_image(movie_link, meta, image_type):
    if os.path.isfile(settings.IMAGE_PATH+movie_link+".jpg"):
        logging.info("File already exists")
    else:
        logging.info("fetching image "+movie_link)
        with open("%s" % (settings.IMAGE_PATH+movie_link+".jpg"), 'wb') as image_file:
            if image_type == "series":
                full_image_url = "http:"+meta['content']
            else:
                full_image_url = meta['content']
            image_request = Request(full_image_url,
                          headers={'User-Agent': 'Mozilla/5.0'})
            image_file.write(urlopen(image_request).read())
            logging.info("Imaged fetched")


def movie_poster(poster_links, movie_title, movie_link, cursor, connect):
    "Fetch movie poster"
    number = re.search(r'\d{4,}', movie_link)
    for url_link in poster_links:
        if re.search(number.group(0), url_link):
            with open("%s" % (settings.IMAGE_PATH+movie_title+".jpg"),'wb') as image_file:
                image_request = Request("http:"+url_link,
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


def get_intervals(cursor, interval, movie, series):
    cursor.execute("SELECT value FROM config WHERE key='update_interval'")
    key = cursor.fetchone()
    value = float(key[0])/3600
    interval.set_text(str(value))
    cursor.execute("SELECT value from config WHERE key='movie_duration'")
    key = cursor.fetchone()
    movie_value = key[0]
    movie.set_text(movie_value)
    cursor.execute("SELECT value from config WHERE key='series_duration'")
    key = cursor.fetchone()
    series_value = key[0]
    series.set_text(series_value)


def process_page(movie_page):
    "find image links from page"
    jpg_posters = []
    for image_jpg in movie_page:
        jpg_posters.append(image_jpg.find('img')['src'])
    return jpg_posters


def movie_compare(cursor, new_list):
    "Compare new move_list with old movie List"
    old_list = []
    cursor.execute('SELECT genre_id,title,link from movies')
    data = cursor.fetchall()
    for old_data in data:
        old_list.append((old_data[0], old_data[1], old_data[2]))
    diff_movies = set(new_list).difference(old_list)
    return diff_movies


def check_url(text, notice, dialog, cursor, connection, link_box):
    "check adding new series"
    if re.search(r'http://www.primewire.ag/(.*)-\d+\-(.*)', text):
        title = re.search(r"http://www.primewire.ag/(.*)-\d+\-(.*)", text)
        change_string = title.group(2)
        show_title = change_string.replace("-", " ")
        logging.info("Inserting new series %s" % show_title)
        try:
            cursor.execute('INSERT INTO series(title,' +
                           'series_link,' +
                           'number_of_episodes,' +
                           'number_of_seasons,' +
                           'status,' +
                           'current_season,' +
                           'last_update)' +
                           ' VALUES(?,?,0,0,1,0,?)',
                           (show_title.title(), text, datetime.now(),))
            connection.commit()
            logging.debug("Series Added: "+show_title)
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


def set_stats(title, connect, cursor, builder):
    cursor.execute("Select series_link,number_of_episodes,number_of_seasons,last_update,status FROM series WHERE title=?",(title,))
    for data in cursor.fetchall():
        link = data[0]
        episodes = str(data[1])
        seasons = str(data[2])
        update = str(data[3])
        status = str(data[4])
    builder.get_object("title").set_text(title)
    builder.get_object('url').set_text(link)
    builder.get_object('episodes').set_text(episodes)
    builder.get_object('seasons').set_text(seasons)
    builder.get_object('update').set_text(update[:10])
    if status == '0':
        builder.get_object('status').set_text("Not Updating")
    else:
        builder.get_object('status').set_text("Updating")


def fetch_current_season(cursor, connection, series_title):
    cursor.execute('SELECT current_season from series where title=?', (series_title,))
    no_season = cursor.fetchone()
    return str(no_season[0])


def star_logging():
    "Start logging"
    if os.path.isdir(settings.DIRECTORY_PATH):
        logging.basicConfig(filename=settings.LOG_FILE_PATH,
                            format='%(asctime)s - %(message)s', filemode='w',
                            level=logging.DEBUG)
    else:
        os.makedirs(settings.DIRECTORY_PATH)


def fetch_movies(cursor, connect):
    cursor.execute("SELECT title,link,id from movies where id >" +
                       '(SELECT cast(value as INTEGER) from config where key="last_movie_id")')
    for movie in cursor.fetchall():
        correct_decode(movie)
        cursor.execute("INSERT INTO movie_images(movie_id, path) " +
                       'VALUES(?,?)', (movie[2],settings.IMAGE_PATH+movie[0]+'.jpg'))
        cursor.execute("UPDATE config set value=? where key='last_movie_id'",
                               (movie[2],))
        connect.commit()


def pre_populate_menu(builder, image):
    image.set_from_file("icons/invert-32.png")
    pixbuf = image.get_pixbuf()
    header_list = builder.get_object('HeaderList')
    header = header_list.append(None, [pixbuf, "Movies"])
    header_list.append(header, [None, "Latest Movies"])
    header_list.append(header, [None, "Movie Archive"])
    image.set_from_file("icons/invert-television.png")
    pixbuf = image.get_pixbuf()
    header = header_list.append(None, [pixbuf, "Series"])
    header_list.append(header, [None, "Latest Episodes"])
    header_list.append(header, [None, "Active Series"])
    header_list.append(header, [None, "Series Archive"])
    image.set_from_file("icons/invert-visible.png")
    pixbuf = image.get_pixbuf()
    header = header_list.append(None, [pixbuf, 'Watch List'])
    header_list.append(header, [None, "Movies"])
    header_list.append(header, [None, "Series"])
