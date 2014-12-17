import logging
from notifylib import settings
from migration.database import Database

logging.getLogger(__name__)

def database_init():
    db = Database(settings.DATABASE_PATH)
    db.initialise()

def database_change():
    db = Database(settings.DATABASE_PATH)
    db.add_change([
        [1, 'CREATE TABLE config(' +
                            'id INTEGER PRIMARY KEY, ' +
                            'key VARCHAR(20) NOT NULL,' +
                             'value VARCHAR(20) NOT NULL)'],
        [2, "CREATE TABLE genre(" +
                            "Id INTEGER PRIMARY KEY," +
                            "genre VARCHAR(10) UNIQUE NOT NULL )"],
        [3, 'CREATE TABLE movies(' +
                            'id INTEGER PRIMARY KEY, ' +
                            'genre_id INTEGER  NOT NULL,' +
                            ' title VARCHAR(20) UNIQUE NOT NULL,' +
                            ' link VARCHAR(20) NOT NULL,' +
                            'date_added TIMESTAMP NOT NULL,' +
                            ' FOREIGN KEY(genre_id) REFERENCES genre(Id) ON UPDATE CASCADE ON DELETE CASCADE)'],
        [4, 'CREATE TABLE series(' +
                            'id INTEGER PRIMARY KEY,' +
                            'title VARCHAR(30) UNIQUE NOT NULL,' +
                            'series_link VARCHAR(60) NOT NULL,' +
                            'number_of_episodes INTEGER NOT NULL,' +
                            'number_of_seasons INTEGER NOT NULL,' +
                            'current_season INTEGER NOT NULL,' +
                            'last_update TIMESTAMP NOT NULL,' +
                            'status BOOLEAN NOT NULL)'],
        [5, 'CREATE TABLE episodes(' +
                            'id INTEGER PRIMARY KEY,' +
                            'series_id INTEGER  NOT NULL,' +
                            'episode_name VARCHAR(15) NOT NULL,' +
                            'episode_link VARCHAR(40) UNIQUE NOT NULL,' +
                            'Date TIMESTAMP,' +
                            ' FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE)'],
        [6, 'CREATE TABLE torrents(' +
                            'Id INTEGER PRIMARY KEY,' +
                            'name VARCHAR(20) UNIQUE NOT NULL,' +
                            'link VARCHAR(20) NOT NULL)' ],
        [7, 'CREATE table series_images(' +
                            'id INTEGER PRIMARY KEY,' +
                            'series_id INTEGER NOT NULL,'
                            'path VARCHAR(20) UNIQUE NOT NULL,' +
                            'FOREIGN KEY (series_id) REFERENCES series(id))'],
        [8, 'CREATE table movie_images(' +
                            'id INTEGER PRIMARY KEY,' +
                            'movie_id INTEGER NOT NULL,' +
                            'path VARCHAR(20) UNIQUE NOT NULL,' +
                            'FOREIGN KEY(movie_id) REFERENCES movies(Id))'],
        [9, "INSERT INTO config(key,value) VALUES('version','0')"],
        [10, "INSERT INTO config(key,value) VALUES('update_interval','3600')"],
        [11, "INSERT INTO config(key,value) VALUES('last_movie_id', '0')"],
        [12, "INSERT INTO config(key,value) VALUES('last_series_id','0')"],
        [13, "INSERT INTO torrents(name,link) VALUES('Kickass','http://kickass.to/usearch/')"],
        [14, "INSERT INTO torrents(name,link) VALUES('The Pirate Bay','http://thepiratebay.se/search/')"],
        [15, "INSERT INTO config(key,value)" +
                                 " VALUES('movie_duration','7')"],
        [16, "INSERT INTO config(key,value)" +
                                 " VALUES('series_duration','7')"],
        [17, "CREATE TABLE watch_queue_status("+
                                "id INTEGER PRIMARY KEY,"+
                                "name VARCHAR(10) UNIQUE NOT NULL)"],
        [18, "CREATE TABLE watch_queue("+
                                "id INTEGER PRIMARY KEY,"+
                                "series_id INTEGER NOT NULL,"+
                                "episode_name VARCHAR(10) UNIQUE NOT NULL,"+
                                "watch_status_id INTEGER NOT NULL,"+
                                "FOREIGN KEY(series_id) REFERENCES series(id),"+
                                "FOREIGN KEY(watch_status_id) REFERENCES watch_queue_status(id))"],
        [19, "ALTER TABLE series ADD COLUMN watch INTEGER NOT NULL DEFAULT 0 "],
        [20, "INSERT INTO watch_queue_status(name) VALUES('new')"],
        [21, "INSERT INTO watch_queue_status(name) VALUES('torrent downloaded')"],
        [22, "INSERT INTO watch_queue_status(name) VALUES('complete')"],
        [23, "DELETE FROM config where id=2"],
        [24, "DELETE FROM config where id=7"]
    ])
