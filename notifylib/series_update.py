#!/usr/bin/python

import urllib2,re
from gi.repository import Notify
from notifylib.notifiy import announce

http="http://www.letmewatchthis.ch"
#Check for latest series episode
def get_episode_count(show_title,show_link,episode_count,cursor,connection):
    """
    Get number of episodes
    Get latest series to send to notification
    update database with lastest series
    """
    count=0
    i=0
    tv_show_page=urllib2.urlopen(str(show_link)).read()
    count_eps=re.findall('<div class="tv_episode_item"> <a href="(.*?)">(.*?)\s+<span',tv_show_page)
    for num_eps in count_eps:
        count+=1 
    if episode_count==0: 
        for data in count_eps:
            populate_all(show_title,data[1],data[0],cursor,connection,http)
            i+=1
            update_number_episodes(cursor,connection,show_title,count)
    elif  episode_count < count: 
        link=http+str(count_eps[-1][0])
        announce("New Series Episode",show_title,link)
        update_number_episodes(cursor,connection,show_title,count)
        insert_difference(show_title,count_eps,count,episode_count,cursor,connection)


def populate_all(show_title,episode_name,episode_link,cursor,connection,http):
    cursor.execute('INSERT INTO episodes(title,episode_name,episode_link) VALUES(?,?,?)' ,(show_title,str(episode_name),http+str(episode_link)))
    connection.commit()

    
def update_number_episodes(cursor,connection,show_title,count):
    cursor.execute("Update series set num_eps=? WHERE title=?",(count,show_title))
    connection.commit()


def insert_difference(show_title,show,web_count,current_count,cursor,connection):
    steps=web_count-current_count
    while steps > 0:
        cursor.execute("INSERT INTO episodes(title,episode_name,episode_link) VALUES(?,?,?)",(show_title,show[-steps][1],http+show[-steps][0]))
        connection.commit()
        steps-=1
    
    
    
def get_series(cursor,connection): #fetch url from database
    cursor.execute('SELECT * FROM series')
    for url in cursor.fetchall():
        get_episode_count(str(url[1]),url[2],url[3],cursor,connection)
    connection.commit()
         

