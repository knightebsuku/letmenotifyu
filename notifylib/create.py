#!/usr/bin/python
import os
from pysqlite2 import dbapi2 as sqlite


database=os.environ['HOME']+'/.local/share/letmenotifyu/letmenotifyu.sqlite'
#database will be made during setup
def make_movie_table(cursor):
    i=0
    cursor.execute('CREATE TABLE movies(id INTEGER PRIMARY KEY, title VARCHAR(20), link VARCHAR(20))')
    while i <=23:
        cursor.execute("INSERT INTO movies VALUES(null,'#####','#####')")
        i+=1

        
def make_series_table(cursor):
     cursor.execute('CREATE TABLE series(id INTEGER PRIMARY KEY,title VARCHAR(15),series_link VARCHAR(20),num_eps INTEGER)')

def make_episode_table(cursor):
    cursor.execute('CREATE TABLE episodes(id INTEGER PRIMARY KEY,title VARCHAR(20),episode_name VARCHAR(15), episode_link VARCHAR(30), FOREIGN KEY (title) REFERENCES series(title))')

def create_database(sqlite_file):
    os.makedirs(os.environ['HOME']+'/.local/share/letmenotifyu/')
    connection=sqlite.connect(sqlite_file)
    cursor=connection.cursor()
    make_movie_table(cursor)
    connection.commit()
    make_series_table(cursor)
    connection.commit()
    make_episode_table(cursor)
    connection.commit()

