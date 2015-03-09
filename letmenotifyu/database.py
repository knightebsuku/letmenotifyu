#!/usr/bin/python3

from letmenotifyu import settings
from litemigration.database import Database

def database_init():
    db = Database('sqlite',database=settings.DATABASE_PATH)
    db.initialise()

def database_change():
    db = Database('sqlite',database=settings.DATABASE_PATH)
    db.add_schema([
        [1, 'CREATE TABLE config(' \
                            'id INTEGER PRIMARY KEY, ' \
                            'key VARCHAR(20) NOT NULL,' \
                             'value VARCHAR(20) NOT NULL)'],
        [2, "CREATE TABLE genre(" \
                            "Id INTEGER PRIMARY KEY," \
                            "genre VARCHAR(10) UNIQUE NOT NULL )"],
        [3, 'CREATE TABLE movies(' \
                            'id INTEGER PRIMARY KEY, ' \
                            'genre_id INTEGER  NOT NULL,' \
                            ' title VARCHAR(20) UNIQUE NOT NULL,' \
                            ' link VARCHAR(20) NOT NULL,' \
                            'date_added TIMESTAMP NOT NULL,' \
                            ' FOREIGN KEY(genre_id) REFERENCES genre(Id) ON UPDATE CASCADE ON DELETE CASCADE)'],
        [4, 'CREATE TABLE series(' \
                            'id INTEGER PRIMARY KEY,' \
                            'title VARCHAR(30) UNIQUE NOT NULL,' \
                            'series_link VARCHAR(60) NOT NULL,' \
                            'number_of_episodes INTEGER NOT NULL,' \
                            'number_of_seasons INTEGER NOT NULL,' \
                            'current_season INTEGER NOT NULL,' \
                            'last_update TIMESTAMP NOT NULL,' \
                            'status BOOLEAN NOT NULL)'],
        [5, 'CREATE TABLE episodes(' \
                            'id INTEGER PRIMARY KEY,' \
                            'series_id INTEGER  NOT NULL,' \
                            'episode_name VARCHAR(15) NOT NULL,' \
                            'episode_link VARCHAR(40) UNIQUE NOT NULL,' \
                            'Date TIMESTAMP,' \
                            ' FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE)'],
        [6, 'CREATE TABLE torrents(' \
                            'Id INTEGER PRIMARY KEY,' \
                            'name VARCHAR(20) UNIQUE NOT NULL,' \
                            'link VARCHAR(20) NOT NULL)' ],
        [7, 'CREATE table series_images(' \
                            'id INTEGER PRIMARY KEY,' \
                            'series_id INTEGER NOT NULL,'
                            'path VARCHAR(20) UNIQUE NOT NULL,' \
                            'FOREIGN KEY (series_id) REFERENCES series(id))'],
        [8, 'CREATE table movie_images(' \
                            'id INTEGER PRIMARY KEY,' \
                            'movie_id INTEGER NOT NULL,' \
                            'path VARCHAR(20) UNIQUE NOT NULL,' \
                            'FOREIGN KEY(movie_id) REFERENCES movies(Id))'],
        [9, "INSERT INTO config(key,value) VALUES('version','0')"],
        [10, "INSERT INTO config(key,value) VALUES('update_interval','3600')"],
        [11, "INSERT INTO config(key,value) VALUES('last_movie_id', '0')"],
        [12, "INSERT INTO config(key,value) VALUES('last_series_id','0')"],
        [13, "INSERT INTO torrents(name,link) VALUES('Kickass','http://kickass.to/usearch/')"],
        [14, "INSERT INTO torrents(name,link) VALUES('The Pirate Bay','http://thepiratebay.se/search/')"],
        [15, "INSERT INTO config(key,value)" \
                                 " VALUES('movie_duration','7')"],
        [16, "INSERT INTO config(key,value)" \
                                 " VALUES('series_duration','7')"],
        [17, "CREATE TABLE watch_queue_status("\
                                "id INTEGER PRIMARY KEY,"\
                                "name VARCHAR(10) UNIQUE NOT NULL)"],
        [18, "CREATE TABLE watch_queue("\
                                "id INTEGER PRIMARY KEY,"\
                                "series_id INTEGER NOT NULL,"\
                                "episode_name VARCHAR(10) UNIQUE NOT NULL,"\
                                "watch_status_id INTEGER NOT NULL,"\
                                "FOREIGN KEY(series_id) REFERENCES series(id),"\
                                "FOREIGN KEY(watch_status_id) REFERENCES watch_queue_status(id))"],
        [19, "ALTER TABLE series ADD COLUMN watch INTEGER NOT NULL DEFAULT 0 "],
        [20, "INSERT INTO watch_queue_status(name) VALUES('new')"],
        [21, "INSERT INTO watch_queue_status(name) VALUES('torrent downloaded')"],
        [22, "INSERT INTO watch_queue_status(name) VALUES('complete')"],
        [23, "CREATE TABLE upcoming_movies("\
         'id INTEGER PRIMARY KEY,'\
         'title VARCHAR(20) UNIQUE NOT NULL,'\
        'link VARCHAR(20) UNIQUE NOT NULL)'],
        [24, "CREATE TABLE upcoming_images("\
         'id INTEGER PRIMARY KEY,'\
         'movie_id INTEGER NOT NULL,'\
         'path VARCHAR(50) UNIQUE NOT NULL,'\
         'FOREIGN KEY(movie_id) REFERENCES upcoming_movies(id))'],
        [25, "DELETE FROM movies"],
        [26,"DROP TABLE movie_images"],
        [27, 'CREATE table movie_images(' \
          'id INTEGER PRIMARY KEY,' \
          'title VARCHAR(20) UNIQUE NOT NULL,' \
          'path VARCHAR(20) UNIQUE NOT NULL)'],
        [28, "DROP TABLE upcoming_images"],
        [29, "CREATE TABLE movie_torrent_links("\
           'id INTEGER PRIMARY KEY,'\
           'movie_id INTEGER UNIQUE NOT NULL,'\
           'link VARCHAR(50) NOT NULL,'\
           'hash_sum VARCHAR(50) NOT NULL,'
           'FOREIGN KEY(movie_id) REFERENCES movies(id))'],
        [30, "DROP TABLE movies"],
        [31, 'CREATE TABLE movies(' \
                            'id INTEGER PRIMARY KEY, ' \
                            'movie_id INTEGER UNIQUE NOT NULL,'
                            'genre_id INTEGER  NOT NULL,' \
                            ' title VARCHAR(20) UNIQUE NOT NULL,' \
                            ' link VARCHAR(20) NOT NULL,' \
                            'date_added TIMESTAMP NOT NULL,' \
                            ' FOREIGN KEY(genre_id) REFERENCES genre(Id) ON UPDATE CASCADE ON DELETE CASCADE)'],
        [32, "ALTER TABLE movies ADD COLUMN hash_sum  VARCHAR NOT NULL DEFAULT 0"],
        [33, "CREATE TABLE movie_queue("\
             'id INTEGER PRIMARY KEY NOT NULL,'\
             'movie_id INTEGER UNIQUE NOT NULL,'\
             'watch_queue_status_id INTEGER NOT NULL,'\
             'FOREIGN KEY(movie_id) REFERENCES movies(id),'\
             'FOREIGN KEY(watch_queue_status_id) REFERENCES watch_queue_status(id))'],
        [34, 'DELETE FROM watch_queue_status'],
        [35, "INSERT INTO watch_queue_status(name) VALUES('new')"],
        [36, "INSERT INTO watch_queue_status(name) VALUES('torrent downloaded')"],
        [37, "INSERT INTO watch_queue_status(name) VALUES('downloading')"],
        [38, "INSERT INTO watch_queue_status(name) VALUES('complete')"],
        [39, "INSERT INTO watch_queue_status(name) VALUES('error downloading')"],
        [40,"CREATE TABLE upcoming_queue("\
         'id INTEGER PRIMARY KEY NOT NULL,'\
         'title VARCHAR(20) UNIQUE NOT NULL,'\
         'FOREIGN KEY(title) REFERENCES upcoming_movies(title))'],
        [41, "DROP TABLE watch_queue"],
        [42, "CREATE TABLE series_queue(" \
          'id INTEGER PRIMARY KEY NOT NULL,' \
          'series_id INTEGER NOT NULL,' \
          'episode_id INTEGER UNIQUE NOT NULL,' \
          'episode_name VARCHAR(20) NOT NULL,' \
          'watch_queue_status_id INTEGER NOT NULL,'\
          'FOREIGN KEY(series_id) REFERENCES series(id),'\
          'FOREIGN KEY(episode_id) REFERENCES episodes(id),'\
          'FOREIGN KEY(watch_queue_status_id) REFERENCES watch_queue_status(id))'],
        [43, "INSERT INTO config(key,value) VALUES('process_interval',600)"],
        [44, "CREATE TABLE series_torrent_links("\
           'id INTEGER PRIMARY KEY NOT NULL,'\
           'series_queue_id INTEGER UNIQUE NOT NULL,'\
           'link VARCHAR(30) NOT NULL,'\
           'FOREIGN KEY(series_queue_id) REFERENCES series_queue(id))'],
        [45,"DELETE FROM config"],
        [46, "INSERT INTO config(key,value) VALUES('update_interval','3600')"],
        [47, "INSERT INTO config(key,value) VALUES('movie_process_interval', '3600')"],
        [48, "INSERT INTO config(key,value) VALUES('series_process_interval','3600')"],
        [49, "INSERT INTO config(key,value) VALUES('movie_duration','7')"],
        [50, "INSERT INTO config(key,value) VALUES('series_duration','7')"],
        [51, "INSERT INTO config(key,value) VALUES('movie_quality','720p')"],
        [52, "INSERT INTO config(key,value) VALUES('max_movie_results','50')"],
        [53, "CREATE TABLE actors("\
         'id INTEGER PRIMARY KEY NOT NULL,' \
         'name VARCHAR(20) UNIQUE NOT NULL,' \
         'actor_link VARCHAR(20) UNIQUE NOT NULL)'],
        [54, "CREATE TABLE movie_details("\
         'id INTEGER PRIMARY KEY NOT NULL,'\
         'movie_id INTEGER UNIQUE NOT NULL,'\
         'language VARCHAR(20) NOT NULL,'\
         'movie_rating REAL NOT NULL,'\
         'youtube_url VARCHAR UNIQUE NOT NULL,'\
         'description VARCHAR(100) NOT NULL,'\
         'FOREIGN KEY(movie_id) REFERENCES movies(id))'],
        [55, "CREATE TABLE actors_movies("\
         'id INTEGER PRIMARY KEY NOT NULL,'\
         'actor_id INTEGER NOT NULL,'\
         'movie_id INTEGER NOT NULL,'\
         'FOREIGN KEY(movie_id) REFERENCES movies(id))'],
        [56, "CREATE TEMPORARY TABLE bk_actors(id INTEGER,name VARCHAR(20))"],
        [57, "INSERT INTO bk_actors SELECT id,name from actors"],
        [58, "DROP TABLE actors"],
        [59, "CREATE TABLE actors("\
          'id INTEGER PRIMARY KEY NOT NULL,'\
          'name VARCHAR(20) UNIQUE NOT NULL)'],
        [60, "INSERT INTO actors SELECT id,name from bk_actors"],
        [61, "DROP TABLE bk_actors"],
        [62, "ALTER TABLE movies ADD COLUMN year INTEGER NOT NULL DEFAULT 0"]
    ])




