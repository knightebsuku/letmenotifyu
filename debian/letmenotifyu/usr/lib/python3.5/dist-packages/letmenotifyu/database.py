import logging
from letmenotifyu import settings
from litemigration.database import Database

log = logging.getLogger(__name__)


def create_movie_db():
    """
    Create Movie database
    """
    log.debug("creating movie database")
    db = Database('sqlite', database=settings.MOVIE_DB)
    db.initialise()


def create_series_db():
    """
    Create series database
    """
    log.debug("creating series database")
    db = Database('sqlite', database=settings.SERIES_DB)
    db.initialise()


def create_general_db():
    """
    Create general database to house global settings for letmenotifyu
    """
    log.debug("creating general database")
    db = Database('sqlite', database=settings.GENERAL_DB)
    db.initialise()


def general_migration():
    log.debug("applying migrations for general database")
    db = Database('sqlite', database=settings.GENERAL_DB)
    db.add_schema([
        [1, 'CREATE TABLE config('
         'id INTEGER PRIMARY KEY,'
         'key TEXT NOT NULL,'
         'value TEXT NOT NULL,'
         'UNIQUE(key,value)) '],
        [2, "INSERT INTO config(key,value) VALUES('update_interval', '3600')"],
        [3, "INSERT INTO config(key,value) VALUES('transmission_host','127.0.0.1')"],
        [4, "INSERT INTO config(key,value) VALUES('transmission_port','9091')"],
        
    ])


def movie_migration():
    """
    Database changes for movie database
    """
    log.debug("applying migrations for movie database")
    db = Database('sqlite', database=settings.MOVIE_DB)
    db.add_schema([
        [1, 'CREATE TABLE config('
         'id INTEGER PRIMARY KEY,'
         'key TEXT NOT NULL,'
         'value TEXT NOT NULL,'
         'UNIQUE(key,value)) '],
        [2, "INSERT INTO config(key, value) VALUES('movie_process_interval', '15')"],
        [3, "INSERT INTO config(key,value) VALUES('movie_duration','7')"],
        [4, "INSERT INTO config(key,value) VALUES('movie_quality','720p')"],
        [5, "INSERT INTO config(key,value) VALUES('max_movie_results','50')"],
        [6, "INSERT INTO config(key,value) VALUES('update_interval','3600')"],
        [7, "INSERT INTO config(key,value) VALUES('imdb_url','http://www.imdb.com/title/')"],
        [8, "INSERT INTO config(key,value) VALUES('youtube_url','https://www.youtube.com/watch?v=')"],
        [9, "INSERT INTO config(key,value) VALUES('transmission_host','127.0.0.1')"],
        [10, "INSERT INTO config(key,value) VALUES('transmission_port','9091')"],
        [11, "CREATE TABLE genre("
         "id INTEGER PRIMARY KEY,"
         "genre TEXT UNIQUE NOT NULL )"],
        [12, 'CREATE TABLE movies('
         'id INTEGER PRIMARY KEY,'
         'yify_id INT UNIQUE NOT NULL,'
         'genre_id INT NOT NULL,'
         'title TEXT UNIQUE NOT NULL,'
         'link TEXT NOT NULL,'
         'date_added TIMESTAMP NOT NULL,'
         'year INT NOT NULL,'
         'FOREIGN KEY(genre_id) REFERENCES genre(id)'
         ' ON UPDATE CASCADE ON DELETE CASCADE)'],
        [13, "CREATE TABLE movie_details("
         'id INTEGER PRIMARY KEY NOT NULL,'
         'movie_id INT UNIQUE NOT NULL,'
         'language TEXT NOT NULL,'
         'movie_rating REAL NOT NULL,'
         'youtube_url TEXT NOT NULL,'
         'description TEXT NOT NULL,'
         'FOREIGN KEY(movie_id) REFERENCES movies(id)'
         'ON UPDATE CASCADE ON DELETE CASCADE)'],
        [14, 'CREATE table movie_images('
         'id INTEGER PRIMARY KEY,'
         'movie_id INT UNIQUE NOT NULL,'
         'path TEXT NOT NULL,'
         'FOREIGN KEY(movie_id) REFERENCES movies(id) ON UPDATE CASCADE ON DELETE CASCADE)' ],
        [15, "CREATE TABLE movie_torrent_links("
         'id INTEGER PRIMARY KEY,'
         'movie_id INT UNIQUE NOT NULL,'
         'link TEXT NOT NULL,'
         'hash_sum TEXT NOT NULL,'
         'transmission_hash TEXT DEFAULT 0,'
         'torrent_name TEXT DEFAULT 0,'
         'FOREIGN KEY(movie_id) REFERENCES movies(id) ON UPDATE CASCADE ON DELETE CASCADE)'],
        [16, "CREATE TABLE watch_queue_status("
         "id INTEGER PRIMARY KEY,"
         "name TEXT UNIQUE NOT NULL)"],
        [17, "INSERT INTO watch_queue_status(name) VALUES('new')"],
        [18, "INSERT INTO watch_queue_status(name) VALUES('torrent downloaded')"],
        [19, "INSERT INTO watch_queue_status(name) VALUES('downloading')"],
        [20, "INSERT INTO watch_queue_status(name) VALUES('complete')"],
        [21, "INSERT INTO watch_queue_status(name) VALUES('error downloading')"],
        [22, "CREATE TABLE movie_queue("
         'id INTEGER PRIMARY KEY,'
         'movie_id INT UNIQUE NOT NULL,'
         'watch_queue_status_id INT NOT NULL DEFAULT 1,'
         'FOREIGN KEY(movie_id) REFERENCES movies(id) ON DELETE CASCADE ON UPDATE CASCADE,'
         'FOREIGN KEY(watch_queue_status_id) REFERENCES watch_queue_status(id))'],
        [23, "CREATE TABLE actors("
         'id INTEGER PRIMARY KEY,'
         'name TEXT UNIQUE NOT NULL)'],
        [24, "CREATE TABLE actors_movies("
         'id INTEGER PRIMARY KEY,'
         'actor_id INT NOT NULL,'
         'movie_id INT NOT NULL,'
         'UNIQUE(actor_id,movie_id),'
         'FOREIGN KEY(movie_id) REFERENCES movies(id) ON DELETE CASCADE ON UPDATE CASCADE,'
         'FOREIGN KEY(actor_id) REFERENCES actors(id) ON DELETE CASCADE ON UPDATE CASCADE)'],
        [25, "DELETE FROM config WHERE key='transmission_host'"],
        [26, "DELETE FROM config WHERE key='transmission_port'"],
    ])
    return


def series_migration():
    """
    Database changes for series database
    """
    log.debug("applying migrations for series database")
    db = Database('sqlite', database=settings.SERIES_DB)
    db.add_schema([
        [1, 'CREATE TABLE config('
         'id INTEGER PRIMARY KEY, '
         'key TEXT NOT NULL,'
         'value TEXT NOT NULL,'
         'UNIQUE(key,value))'],
        [2, "INSERT INTO config(key,value) VALUES('update_interval','3600')"],
        [3, "INSERT INTO config(key,value) VALUES('series_process_interval','15')"],
        [4, "INSERT INTO config(key,value) VALUES('series_duration','7')"],
        [5, "INSERT INTO config(key,value) VALUES('transmission_host','127.0.0.1')"],
        [6, "INSERT INTO config(key,value) VALUES('transmission_port','9091')"],
        [7, 'CREATE TABLE series('
         'id INTEGER PRIMARY KEY,'
         'title TEXT NOT NULL,'
         'series_link TEXT UNIQUE NOT NULL,'
         'number_of_episodes INT NOT NULL,'
         'number_of_seasons INT NOT NULL,'
         'current_season INT NOT NULL,'
         'last_update TIMESTAMP NOT NULL,'
         'status BOOLEAN NOT NULL DEFAULT t,'
         'watch BOOLEAN NOT NULL DEFAULT t)'],
        [8, 'CREATE table series_images('
         'id INTEGER PRIMARY KEY,'
         'series_id INT NOT NULL,'
         'path TEXT UNIQUE NOT NULL,'
         'FOREIGN KEY (series_id) REFERENCES series(id) ON UPDATE CASCADE ON DELETE CASCADE)'],
        [9, 'CREATE TABLE episodes('
         'id INTEGER PRIMARY KEY,'
         'series_id INT  NOT NULL,'
         'episode_name TEXT NOT NULL,'
         'episode_number TEXT NOT NULL,'
         'episode_link TEXT UNIQUE NOT NULL,'
         'date TIMESTAMP,'
         ' FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE ON UPDATE CASCADE)'],
        [10, "CREATE TABLE watch_queue_status("
         "id INTEGER PRIMARY KEY,"
         "name TEXT UNIQUE NOT NULL)"],
        [11, "INSERT INTO watch_queue_status(name) VALUES('new')"],
        [12, "INSERT INTO watch_queue_status(name) VALUES('torrent downloaded')"],
        [13, "INSERT INTO watch_queue_status(name) VALUES('downloading')"],
        [14, "INSERT INTO watch_queue_status(name) VALUES('complete')"],
        [15, "INSERT INTO watch_queue_status(name) VALUES('error downloading')"],
        [16, "CREATE TABLE series_queue("
         'id INTEGER PRIMARY KEY,'
         'series_id INT NOT NULL,'
         'episode_id INT UNIQUE NOT NULL,'
         'episode_name TEXT NOT NULL,'
         'watch_queue_status_id INT NOT NULL DEFAULT 1,'
         'FOREIGN KEY(series_id) REFERENCES series(id) ON DELETE CASCADE ON UPDATE CASCADE,'
         'FOREIGN KEY(episode_id) REFERENCES episodes(id),'
         'FOREIGN KEY(watch_queue_status_id) REFERENCES watch_queue_status(id))'],
        [17, "CREATE TABLE series_torrent_links("
         'id INTEGER PRIMARY KEY,'
         'series_queue_id INT UNIQUE NOT NULL,'
         'link TEXT NOT NULL,'
         'transmission_hash TEXT DEFAULT 0,'
         'torrent_name TEXT DEFAULT 0,'
         'FOREIGN KEY(series_queue_id) REFERENCES series_queue(id) ON UPDATE CASCADE ON DELETE CASCADE)'],
        [18, "INSERT INTO config(key,value) VALUES('imdb_url','http://www.imdb.com/title/')"],
        [19, "INSERT INTO config(key,value) VALUES('youtube_url','https://www.youtube.com/watch?v=')"],
    ])
