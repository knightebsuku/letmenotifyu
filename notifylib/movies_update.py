#!/usr/bin/env python

import urllib2
import  re
import sys
from gi.repository import Notify
from notifylib.notifiy import announce
from pysqlite2 import dbapi2 as sqlite

sqlite_file='/home/zeref/Coding/Python/letmenotifyu/letmenotifyu-1.2/notifylib/letmenotifyu.sqlite'

def get_movies(cursor,connection):
    """
     Get latest movies from site
     """
    new_store=[""]*24
    movie_links=[""]*24 
    count=0
    response=urllib2.urlopen('http://www.letmewatchthis.ch/index.php?sort=featured').read()
    latest_movies=re.findall('<div class="index_item index_item_ie"><a href=(.*?) title="Watch (.*?)">',response)
    for new in latest_movies:
        new_store[count]=new[1]
        movie_links[count]=new[0]
        count+=1
    compare(new_store,movie_links,cursor,connection)
           
def compare(new_movie,new_link,cursor,connection):
     cursor.execute("SELECT title FROM movies WHERE id=1")
     for top_list in cursor.fetchall():
            link="http://www.letmewatchthis.ch"+new_link[0][1:][:-1]
            if top_list[0]!=new_movie[0]:
                announce('New Movie',new_movie[0],link)
                update_database(new_movie,new_link,cursor,connection)
                


def update_database(update_movie,update_link,cursor,connection): 
    count,index=1,0
    for movie in update_movie:
        link="http://www.letmewatchthis.ch"+update_link[index][1:][:-1]
        cursor.execute('UPDATE movies SET title=?,link=? WHERE id=?',(movie,link,count))
        connection.commit()
        count+=1
        index+=1



