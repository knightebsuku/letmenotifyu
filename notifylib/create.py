#!/usr/bin/python3

import sqlite3 as sqlite

def make_movie_table(cursor):
    cursor.execute('CREATE TABLE movies(id INTEGER PRIMARY KEY, title VARCHAR(20), link VARCHAR(20))')
    
def make_series_table(cursor):
     cursor.execute('CREATE TABLE series(title VARCHAR(30) PRIMARY KEY,series_link VARCHAR(60),number_of_episodes INTEGER,number_of_seasons INTEGER)')

def make_episode_table(cursor):
    cursor.execute('CREATE TABLE episodes(id INTEGER PRIMARY KEY,title VARCHAR(30),episode_name VARCHAR(15), episode_link VARCHAR(40), Date TIMESTAMP, FOREIGN KEY (title) REFERENCES series(title) ON DELETE CASCADE)')

def alter_tables(cursor):
    cursor.execute('ALTER TABLE series ADD COLUMN last_update TIMESTAMP,status BOOLEAN')
    #function to change database if needed.

def create_database(sqlite_file):
    connection = sqlite.connect(sqlite_file)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    connection.commit()
    make_movie_table(cursor)
    connection.commit()
    make_series_table(cursor)
    connection.commit()
    make_episode_table(cursor)
    connection.commit()
    connection.close()

