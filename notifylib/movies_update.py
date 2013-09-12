#!/usr/bin/python3

import re

from urllib.request import Request, urlopen
from notifylib.notifiy import announce

def get_movies(cursor, connection):
    """extract movie links and titles"""
    new_movie_info = {}
    req = Request('http://www.primewire.ag/index.php?sort=featured',
                headers = {'User-Agent':'Mozilla/5.0'})
    latest_movie_page= urlopen(req).read().decode('utf-8')
    latest_movies = re.findall(r'<div class="index_item index_item_ie"><a href="(.*?)" title="Watch (.*?)">',
                               latest_movie_page)
    for new_info in latest_movies: 
        new_movie_info[new_info[1]] = new_info[0]
    compare(new_movie_info, cursor, connection)
        
           
def compare(new_movie_info, cursor, connection):
    """Compare old movie list to new movie list"""
    old_movie_info = {}
    insert_movies=[]
    http = 'http://primewire.ag'
    cursor.execute("SELECT title FROM movies")
    for top_movie in cursor.fetchall():
        old_movie_info[top_movie[0]] = ""
    diff_titles = set(new_movie_info.keys()) - set(old_movie_info.keys())
    if  diff_titles:
        for title in list(diff_titles):
            announce('New Movie',title, http+new_movie_info[title])
            insert_movies.append((title, http+new_movie_info[title]))
        cursor.executemany("INSERT INTO movies(title,link) VALUES(?,?)",insert_movies)
        connection.commit()
