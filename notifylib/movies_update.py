#!/usr/bin/env python

import urllib2, re,sys
from gi.repository import Notify
from pysqlite2 import dbapi2 as sqlite
from notifylib.notifiy import announce
#check for latest movies
def get_movies(movie_db): # Get latest movies from site
        new_store=[""]*24 #max of 24 movies are displayed on the page
        movie_links=[""]*24 
        count=0
        response=urllib2.urlopen('http://www.1channel.ch/index.php?sort=featured').read()
        latest_movies=re.findall('<div class="index_item index_item_ie"><a href=(.*?) title="Watch (.*?)">',response)
        for new in latest_movies:
            new_store[count]=new[1]
            movie_links[count]=new[0]
            count+=1
        compare(new_store,movie_links,movie_db)
           
def compare(new_movie,new_link,movie_db): #compare latest from site and database
     connection=sqlite.connect(movie_db)
     db=connection.cursor()
     db.execute("SELECT titles FROM movie WHERE id=1")
     for top_list in db.fetchall():
            link="http://www.1channel.ch"+new_link[0][1:][:-1]
            if top_list[0]!=new_movie[0]:
		announce('New Movie',new_movie[0],link)
                #update_fuc(new_movie[0],link)
                update_db(new_movie,new_link,db)
                connection.commit()
                


def update_db(update_movie,update_link,db): #update Database
    count,index=1,0
    for movie in update_movie: #update movie database
        link="http://www.1channel.ch"+update_link[index][1:][:-1]
        #plot=plot_db(link)
        db.execute('UPDATE movie SET titles=?,link=? WHERE id=?',(movie,link,count))
        count+=1
        index+=1




