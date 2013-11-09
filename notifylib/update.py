
import re
import time
import sqlite3
from urllib.request import Request, urlopen
from notifylib.notifiy import announce
from datetime import datetime


def get_series(cursor,connect):
    cursor.execute('SELECT title,series_link,number_of_episodes FROM series WHERE status = 1 ')
    for url in cursor.fetchall():
        get_episode_count(url[0], url[1], url[2], cursor, connect)


def get_movies(cursor,connect):
    new_movie_info = {}
    req = Request('http://www.primewire.ag/index.php?sort=featured',
                  headers = {'User-Agent':'Mozilla/5.0'})
    latest_movie_page= urlopen(req).read().decode('utf-8')
    latest_movies = re.findall(r'<div class="index_item index_item_ie"><a href="(.*?)" title="Watch (.*?)">', latest_movie_page)
    for new_info in latest_movies:
        new_movie_info[new_info[1]] = new_info[0]
    compare(new_movie_info, cursor, connect)

def get_updates(db_file):
    connect=sqlite3.connect(db_file)
    cursor=connect.cursor()
    while True:
            try:
                    get_movies(cursor,connect)
                    get_series(cursor,connect)
                    time.sleep(21600)
            except Exception as e:
                    time.sleep(300)
                                          

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


def get_episode_count(show_title, show_link, episode_count, cursor, connection):
    episode_detail=[]
    new_series_detail=[]
    
    req= Request(show_link, headers = {'User_Agent':'Mozlla/5.0'})
    tv_show_webpage = urlopen(req).read().decode('ISO-8859-1')
    all_episodes = re.findall(r'<div class="tv_episode_item"> <a href="(.*?)">(.*?)\s+<',
                              tv_show_webpage)
    seasons = re.findall(' <h2><a href="(.*?)"', tv_show_webpage)
    
    for ep in all_episodes:
        update_data=(show_title,)+ep+(str(datetime.now()),)
        episode_detail.append(update_data)
        
        new_series_data=(show_title,)+ep
        new_series_detail.append(new_series_data)

    if episode_count == 0:
        new_series_add(new_series_detail, cursor, connection)
        update_series_table( len(all_episodes), len(seasons),
                               show_title, cursor, connection)
    elif  episode_count < len(all_episodes):
        http='www.primewire.ag'
        announce("New Series Episodes",show_title,http+all_episodes[-1][0])
        update_series_table( len(all_episodes), len(seasons), show_title,
                                cursor,connection)
        insert_difference(show_title, all_episodes, len(all_episodes),
                          episode_count, cursor, connection)
    else:
        cursor.execute("UPDATE series SET last_update=? WHERE title=?",
                       (datetime.now(),show_title,))
        connection.commit()

def new_series_add(new_series_detail, cursor, connection):
    """Add new series"""
    cursor.executemany('INSERT INTO episodes(title,episode_link,episode_name) VALUES(?,?,?)' ,
                       new_series_detail)
    connection.commit()
    
def update_series_table(num_episodes, num_seasons, show_title,
                           cursor, connection):
    """Update The number of episodes and seasons"""
    cursor.execute("Update series set number_of_episodes=?,number_of_seasons=?,last_update=? WHERE title=?",
                   (num_episodes,num_seasons,datetime.now(), show_title,))
    connection.commit()

def insert_difference(show_title, all_episodes, web_count, db_count, cursor,
                      connection):
    """Insert only the new episodes"""
    steps = web_count-db_count
    while steps > 0:
        cursor.execute("INSERT INTO episodes(title,episode_name,episode_link,Date) VALUES(?,?,?,?)",
                       (show_title, all_episodes[-steps][1], all_episodes[-steps][0],datetime.now(),))
        connection.commit()
        steps-=1
