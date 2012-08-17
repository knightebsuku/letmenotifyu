#!/usr/bin/python
import os
from pysqlite2 import dbapi2 as sqlite

#database will be made during setup
def make_movie_db(db):
    i=0
    connection=sqlite.connect(db)
    db=connection.cursor()
    db.execute('CREATE TABLE movie(id INTEGER PRIMARY KEY,titles VARCHAR(20),link VARCHAR(20))')
    connection.commit()
    while i <=23:
        db.execute("INSERT INTO movie VALUES(null,'#####','#####')")
        connection.commit()
        i+=1

        
def make_series_db(db):
     connection=sqlite.connect(db)
     cursor=connection.cursor()
     cursor.execute('CREATE TABLE series(id INTEGER PRIMARY KEY,url VARCHAR(30),num_eps INTEGER)')
     connection.commit()

def create_db(movie_db,series_db):
    make_movie_db(movie_db)
    make_series_db(series_db)


movie_path=os.environ['HOME']+'/.local/share/letmenotifyu/movies.db'
series_path=os.environ['HOME']+'/.local/share/letmenotifyu/url.db'
#create_db(movie_path,series_path)
