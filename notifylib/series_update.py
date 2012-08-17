#!/usr/bin/env python

import urllib2,re
from gi.repository import Notify
from pysqlite2 import dbapi2 as sqlite
from notifylib.notifiy import announce


#Check for latest series episode
def get_episode_count(tv_show_url,ep_counts,series_db,cursor):#count number of episodes
        count=0
        ep_link=[""]
        http="http://www.1channel.ch"
        check=urllib2.urlopen(tv_show_url).read()
        num_eps=re.findall('<div class="tv_episode_item"> <a href=(.*?)>',check)
        for amount in num_eps:
            count+=1
        if ep_counts < count:
            link=http+amount[1:][:-1]
            announce("New Series Episode",link)
            #update database
            #connection=sqlite.connect(series_db)
            #cursor=connection.cursor()
            cursor.execute('UPDATE series SET num_eps=? WHERE url=?',(count,tv_show_url))
           
            
            
def get_series(series_db): #fetch url from database
    connection=sqlite.connect(series_db)
    cursor=connection.cursor()
    cursor.execute('SELECT * FROM series')
    for url in cursor.fetchall():
         get_episode_count(url[1],url[2],series_db,cursor)
    connection.commit()
         

     

