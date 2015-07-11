#!/usr/bin/python3

from letmenotifyu import settings
from litemigration.database import Database


def database_init():
    db = Database('postgresql', database=settings.DB_NAME,
                  user=settings.DB_USER,
                  password=settings.DB_PASSWORD,
                  host=settings.DB_HOST,
                  port=settings.DB_PORT)
    db.initialise()


def database_change():
    db = Database('postgresql', database=settings.DB_NAME,
                  user=settings.DB_USER,
                  password=settings.DB_PASSWORD,
                  host=settings.DB_HOST,
                  port=settings.DB_PORT)
    db.add_schema([
        [1, 'CREATE TABLE config(' \
                            'id SERIAL PRIMARY KEY, ' \
                            'key TEXT NOT NULL,' \
                            'value TEXT NOT NULL,'\
                            'UNIQUE(key,value))'],
        [2, "INSERT INTO config(key,value) VALUES('update_interval','3600')"],
        [3, "INSERT INTO config(key,value) VALUES('movie_process_interval', '15')"],
        [4, "INSERT INTO config(key,value) VALUES('series_process_interval','15')"],
        [5, "INSERT INTO config(key,value) VALUES('movie_duration','7')"],
        [6, "INSERT INTO config(key,value) VALUES('series_duration','7')"],
        [7, "INSERT INTO config(key,value) VALUES('movie_quality','720p')"],
        [8, "INSERT INTO config(key,value) VALUES('max_movie_results','50')"],
        [9, "CREATE TABLE genre(" \
                            "id SERIAL PRIMARY KEY," \
                            "genre TEXT UNIQUE NOT NULL )"],
        [10, 'CREATE TABLE movies(' \
                            'id SERIAL PRIMARY KEY,' \
                            'yify_id INT UNIQUE NOT NULL,'\
                            'genre_id INT  NOT NULL,' \
                            'title TEXT UNIQUE NOT NULL,' \
                            'link TEXT NOT NULL,' \
                            'date_added TIMESTAMP NOT NULL,' \
                            'year INT NOT NULL,'\
                            'FOREIGN KEY(genre_id) REFERENCES genre(id) ON UPDATE CASCADE ON DELETE CASCADE)'],
        [11, "CREATE TABLE movie_details("\
                            'id SERIAL PRIMARY KEY NOT NULL,'\
                            'movie_id INT UNIQUE NOT NULL,'\
                            'language TEXT NOT NULL,'\
                            'movie_rating REAL NOT NULL,'\
                            'youtube_url TEXT NOT NULL,'\
                            'description TEXT NOT NULL,'\
                            'FOREIGN KEY(movie_id) REFERENCES movies(id) ON UPDATE CASCADE ON DELETE CASCADE)'],
        [12, 'CREATE table movie_images(' \
                            'id serial PRIMARY KEY,' \
                            'title TEXT NOT NULL,'\
                            'path TEXT NOT NULL,'\
                            'UNIQUE(title,path))' ],
        [13, "CREATE TABLE movie_torrent_links("\
                           'id SERIAL PRIMARY KEY,'\
                           'movie_id INT UNIQUE NOT NULL,'\
                           'link TEXT NOT NULL,'\
                           'hash_sum TEXT NOT NULL,'
                           'FOREIGN KEY(movie_id) REFERENCES movies(id) ON UPDATE CASCADE ON DELETE CASCADE)'],
        [14, "CREATE TABLE upcoming_movies("\
                           'id SERIAL PRIMARY KEY,'\
                           'title TEXT UNIQUE NOT NULL,'\
                           'link TEXT UNIQUE NOT NULL,'\
                           'UNIQUE(title,link))'],
        [15, 'CREATE TABLE series(' \
                            'id SERIAL PRIMARY KEY,' \
                            'title TEXT NOT NULL,' \
                            'series_link TEXT UNIQUE NOT NULL,' \
                            'number_of_episodes INT NOT NULL,' \
                            'number_of_seasons INT NOT NULL,' \
                            'current_season INT NOT NULL,' \
                            'last_update TIMESTAMP NOT NULL,' \
                            'status BOOLEAN NOT NULL,'\
                             'watch BOOLEAN NOT NULL)'],
        [16, 'CREATE table series_images(' \
                            'id SERIAL PRIMARY KEY,' \
                            'series_id INT NOT NULL,'
                            'path TEXT UNIQUE NOT NULL,' \
                            'FOREIGN KEY (series_id) REFERENCES series(id) ON UPDATE CASCADE ON DELETE CASCADE)'],
        [17, 'CREATE TABLE episodes(' \
                            'id SERIAL PRIMARY KEY,' \
                            'series_id INT  NOT NULL,' \
                            'episode_name TEXT NOT NULL,' \
                            'episode_number TEXT NOT NULL,'\
                            'episode_link TEXT UNIQUE NOT NULL,' \
                            'date TIMESTAMP,' \
                            ' FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE ON UPDATE CASCADE)'],
        [18, "CREATE TABLE watch_queue_status("\
                                "id SERIAL PRIMARY KEY,"\
                                "name TEXT UNIQUE NOT NULL)"],
        [19, "INSERT INTO watch_queue_status(name) VALUES('new')"],
        [20, "INSERT INTO watch_queue_status(name) VALUES('torrent downloaded')"],
        [21, "INSERT INTO watch_queue_status(name) VALUES('downloading')"],
        [22, "INSERT INTO watch_queue_status(name) VALUES('complete')"],
        [23, "INSERT INTO watch_queue_status(name) VALUES('error downloading')"],
        [24, "CREATE TABLE series_queue(" \
                                'id SERIAL PRIMARY KEY,' \
                                'series_id INT NOT NULL,' \
                                'episode_id INT UNIQUE NOT NULL,' \
                                'episode_name TEXT NOT NULL,' \
                                'watch_queue_status_id INT NOT NULL,'\
                                'FOREIGN KEY(series_id) REFERENCES series(id) ON DELETE CASCADE ON UPDATE CASCADE,'\
                                'FOREIGN KEY(episode_id) REFERENCES episodes(id),'\
                                'FOREIGN KEY(watch_queue_status_id) REFERENCES watch_queue_status(id))'],
        [25, "CREATE TABLE series_torrent_links("\
                            'id SERIAL PRIMARY KEY,'\
                            'series_queue_id INT UNIQUE NOT NULL,'\
                            'link TEXT NOT NULL,'\
                            'FOREIGN KEY(series_queue_id) REFERENCES series_queue(id) ON UPDATE CASCADE ON DELETE CASCADE)'],
        [26, 'CREATE TABLE torrents(' \
                            'Id SERIAL PRIMARY KEY,' \
                            'name TEXT UNIQUE NOT NULL,' \
                            'link TEXT NOT NULL)' ],
        [27, "CREATE TABLE movie_queue("\
                                'id SERIAL PRIMARY KEY,'\
                                'movie_id INT UNIQUE NOT NULL,'\
                                'watch_queue_status_id INT NOT NULL,'\
                                'FOREIGN KEY(movie_id) REFERENCES movies(id) ON DELETE CASCADE ON UPDATE CASCADE,'\
                                'FOREIGN KEY(watch_queue_status_id) REFERENCES watch_queue_status(id))'],
        [28, "CREATE TABLE upcoming_queue("\
                                'id SERIAL PRIMARY KEY,'\
                                'title TEXT UNIQUE NOT NULL,'\
                                'FOREIGN KEY(title) REFERENCES upcoming_movies(title) ON DELETE CASCADE ON UPDATE CASCADE)'],
        [29, "CREATE TABLE actors("\
                                'id SERIAL PRIMARY KEY,' \
                                'name TEXT UNIQUE NOT NULL)'],
        [30, "CREATE TABLE actors_movies("\
                                 'id SERIAL PRIMARY KEY,'\
                                 'actor_id INTEGER NOT NULL,'\
                                 'movie_id INTEGER NOT NULL,'\
                                 'UNIQUE(actor_id,movie_id),'\
                                 'FOREIGN KEY(movie_id) REFERENCES movies(id))'],
        [31, "INSERT INTO config(key,value) VALUES('imdb_url','http://www.imdb.com/title/')"],
        [32, "INSERT INTO config(key,value) VALUES('youtube_url','https://www.youtube.com/watch?v=')"],
        [33, "ALTER TABLE series_torrent_links ADD COLUMN torrent_hash TEXT DEFAULT '0'"],
        [34, "ALTER TABLE movie_torrent_links ADD COLUMN transmission_hash TEXT DEFAULT '0'"],
        [35, "ALTER TABLE movie_torrent_links ADD COLUMN torrent_name TEXT DEFAULT '0'"],
        [36, "ALTER TABLE series_torrent_links ADD COLUMN transmission_hash TEXT DEFAULT '0'"],
        [37, "ALTER TABLE series_torrent_links ADD COLUMN torrent_name TEXT DEFAULT '0'"],
        [38, "INSERT INTO config(key,value) VALUES('transmission_host','127.0.0.1')"],
        [39, "INSERT INTO config(key,value) VALUES('transmission_port','9091')"]
        
    ])
