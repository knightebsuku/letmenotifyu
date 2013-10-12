#!/usr/bin/python3

import sqlite3 as sqlite

from datetime import datetime
def make_movie_table(cursor):
    cursor.execute('CREATE TABLE movies(id INTEGER PRIMARY KEY, title VARCHAR(20), link VARCHAR(20))')

def make_series_table(cursor):
     cursor.execute('CREATE TABLE series(title VARCHAR(30) PRIMARY KEY,series_link VARCHAR(60),number_of_episodes INTEGER,number_of_seasons INTEGER)')

def make_episode_table(cursor):
    cursor.execute('CREATE TABLE episodes(id INTEGER PRIMARY KEY,title VARCHAR(30),episode_name VARCHAR(15), episode_link VARCHAR(40), Date TIMESTAMP, FOREIGN KEY (title) REFERENCES series(title) ON DELETE CASCADE)')

def make_version_table(cursor):
    cursor.execute('CREATE TABLE schema_version(version VARCHAR(6))')
    cursor.execute('INSERT INTO schema_version(version) VALUES ("1.7.1")')



def create_database(sqlite_file):
    connection = sqlite.connect(sqlite_file)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    make_movie_table(cursor)
    make_series_table(cursor)
    make_episode_table(cursor)
    make_version_table(cursor)
    connection.commit()
    connection.close()


def upgrade_database(sqlite_file):
    connect= sqlite.connect(sqlite_file)
    cursor= connect.cursor()
    cursor.execute("SELECT version FROM schema_version")
    row=cursor.fetchone()
    database_version= row[0]
    
    if database_version=='1.7.0':
        print("Need to upgrade to version 1.7.1")
        try:
            cursor.execute("ALTER TABLE series ADD COLUMN last_update TIMESTAMP")
            cursor.execute("UPDATE series set last_update=? ",(datetime.now(),))
            connect.commit()
            cursor.execute("ALTER TABLE series ADD COLUMN status BOOLEAN")
            cursor.execute("UPDATE series set status=1")
            connect.commit()
            cursor.execute("UPDATE schema_version SET version='1.7.1' WHERE id=1")
            connect.commit()
            database_version="1.7.1"
            print("Datebase Updated")
        except Exception as e:
            print(e)
            print("Unable to update Database")
        finally:
            connect.close()


        
        
        
    
