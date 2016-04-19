"""
Get details about movies eg release date cast etc
"""

import sqlite3
import requests
import logging

from . import settings
from bs4 import BeautifulSoup as Soup

def poll_movie_detail():
    conn = sqlite3.connect(settings.MOVIE_DB_PATH)
    c = conn.cursor()

    c.execute("SELECT movie_id,detail_queue_status_id, kickass_url"\
              " FROM movie_detail_queue mdq join movie"\
              " on movie.id=mdq.movie_id WHERE detail_queue_status_id = 1")
    for q in c.fetchall():
        # go to page and get movie details and place in queue for insert
        pass
    conn.close()
    

def get_detail(url):
    try:
        detail = []
        req = requests.get(url)
        html_page = Soup(req.text, 'lxml')
        movie_info = html_page.find('div',{'class':'dataList'})
        line_items = movie_info.find_all('li')
        for li in line_items:
            if li.find('strong').text == 'IMDb link:':
                imdb_link = li.find('a')['href']
                detail.append(imdb_link)
            if li.fing('strong').text == 'IMDb rating:':
                rating = li.text
                detail.append(rating)
            if li.find('strong').text == 'Genre:':
                genre = li.find('a').text
                detail.append(genre)
            if li.find('strong').text == 'Release date:':
                release_date = li.text
                detail.append(release_date)
        cast_list = cast(movie_info)
        summarys = summary(html_page)
        insert(cast_list, summarys, detail)
    except Exception as e:
        print(e)


def cast(html_page):
    "get list of all actors"
    span_cast = html_page.find('div', {'class':'floatleft width100perc botmarg10px' })
    for actor in span_cast.find_all('span'):
        print(actor.text)
    return ""
    

def summary(html_page):
    paragraph = html_page.find('p',
                                {'class': 'accentbox botmarg10px'})
    return paragraph.text


def insert(cast, summary, detail, movie_id):
    conn = sqlite3.connect(settings.MOVIE_DB_PATH)
    c = conn.cursor()
    try:
        for actor in cast:
            c.execute("INSERT INTO cast(name) VALUES(?)", (actor,))
            c.execute("INSERT INTO movie_cast(movie_id, actor_id)"\
                      " VALUES(?,?)", (movie_id, c.lastrowid))
        c.execute("INSERT INTO detail(imdb_link, imdb_rating, genre, release date) VALUES(?,?,?,?,?)",
                  (detail[0], detail[1], detail[2], detail[3], summary))
        c.commit()
    except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
        logging.error(e)
