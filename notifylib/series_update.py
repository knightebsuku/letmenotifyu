#!/usr/bin/python3

from  urllib.request import Request, urlopen
import re
from notifylib.notifiy import announce

def get_episode_count(show_title, show_link, episode_count, cursor, connection):
    """
    Get number of episodes
    Get latest series to send to notification
    update database with lastest series
    """
    #title = re.search(r'(.*)/tv', show_link) or re.search(r'(.*)/watch', show_link)
    #http = title.group(1)
    count, count_seasons, i = 0
    req= Request(show_link,headers = {'User_Agent':'Mozlla/5.0'})
    tv_show_webpage = urlopen(req).read()
    all_epsisodes = re.findall('<div class="tv_episode_item"> <a href="(.*?)">(.*?)\s+<', tv_show_webpage)
    seasons = re.findall(' <h2><a href=(.*?)', tv_show_webpage)
    for seasons_count in seasons:
        count_seasons += 1
    for num_eps in all_epsisodes:
        count+= 1 
    if episode_count == 0: 
        for data in all_episodes:
            new_series_add(show_title, data[1], data[0], cursor, connection, http)
            i+= 1
            update_number_episodes(cursor, connection, show_title,
                                   count, count_seasons)
    elif  episode_count < count: 
        link = http+str(count_eps[-1][0])
        announce("New Series Episode", show_title, link)
        update_number_episodes(cursor, connection, show_title, count, count_seasons)
        insert_difference(show_title, count_eps, count, episode_count, cursor,
                          connection, http)

def new_series_add(show_title, episode_name, episode_link, cursor, connection, http):
    cursor.execute('INSERT INTO episodes(title,episode_name,episode_link) VALUES(?,?,?)' , (show_title, str(episode_name), http+str(episode_link)))
    connection.commit()
    
def update_number_episodes(cursor, connection, show_title, count, seasons):
    cursor.execute("Update series set number_of_episodes=?,number_of_seasons=? WHERE title=?", (count, seasons, show_title))
    connection.commit()

def insert_difference(show_title, show, web_count, current_count, cursor,
                      connection, http):
    steps = web_count-current_count
    while steps > 0:
        cursor.execute("INSERT INTO episodes(title,episode_name,episode_link) VALUES(?,?,?)", (show_title, show[-steps][1], http+show[-steps][0]))
        connection.commit()
        steps-=1
        
def get_series(cursor, connection): #fetch url from database
    cursor.execute('SELECT * FROM series')
    for url in cursor.fetchall():
        get_episode_count(str(url[0]), url[1], url[2], cursor, connection)
         

