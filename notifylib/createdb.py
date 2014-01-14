
import sqlite3
import logging
from datetime import datetime


logging.getLogger(__name__)


class Database:
    def __init__(self,db_file):
        self.db_file = db_file
        self.connect = sqlite3.connect(self.db_file)
        self.cursor = self.connect.cursor()
        
    def create_database(self):
        logging.info("Creating new Database")
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.cursor.execute('CREATE TABLE movies(id INTEGER PRIMARY KEY, title VARCHAR(20), link VARCHAR(20))')
        self.cursor.execute('CREATE TABLE series(title VARCHAR(30) PRIMARY KEY,series_link VARCHAR(60),number_of_episodes INTEGER,number_of_seasons INTEGER,last_update TIMESTAMP,status BOOLEAN)')
        self.cursor.execute('CREATE TABLE episodes(id INTEGER PRIMARY KEY,title VARCHAR(30),episode_name VARCHAR(15), episode_link VARCHAR(40), Date TIMESTAMP, FOREIGN KEY (title) REFERENCES series(title) ON DELETE CASCADE)')
        self.cursor.execute('CREATE TABLE schema_version(id IINTEGER PRIMARY KEY,version VARCHAR(6))')
        self.cursor.execute('INSERT INTO schema_version(version) VALUES ("1.7.2")')
        self.connect.commit()
        logging.info("Database has been created")

    def upgrade_database(self):
        try:
            self.cursor.execute("SELECT version FROM schema_version")
            rows = self.cursor.fetchone()
            database_version = rows[0]
            
            if database_version == '1.7.2':
                logging.debug("Upgrading to version 1.7.3")
                self.cursor.execute("CREATE TABLE torrents(Id INTEGER PRIMARY KEY,name VARCHAR(20),link VARCHAR(20))")
                self.cursor.execute("INSERT INTO torrents(name) VALUES('http://kickass.to/usearch/')")
                self.connect.commit()
                self.cursor.execute("INSERT INTO torrents(name) VALUES('http://thepiratebay.sx/search/')")
                self.connect.commit()
                self.cursor.execute("INSERT INTO torrents(name) VALUES('http://isohunt.to/torrents/?ihq=')")
                self.connect.commit()
                self.cursor.execute("UPDATE schema_version set version='1.7.3' where id=1")
                self.connect.commit()
                database_version = '1.7.3'
                
            if database_version == '1.7.3':
                logging.debug("need to upgrade to 1.8.0")
                self.cursor.execute('DROP table schema_version')
                self.cursor.execute("CREATE TABLE config(id INTEGER PRIMARY KEY, key VARCHAR(20), value VARCHAR(20))")
                self.cursor.execute("INSERT INTO config(key,value)  VALUES('version','1.8.0')")
                self.connect.commit()
                self.cursor.execute("INSERT INTO config(key,value) VALUES('update_interval','3600')")
                self.connect.commit()
                self.cursor.execute("DROP TABLE movies")
                self.connect.commit()
                self.cursor.execute('CREATE TABLE movies(Id INTEGER PRIMARY KEY, genre_id INTEGER  NOT NULL, title VARCHAR(20) UNIQUE NOT NULL, link VARCHAR(20) NOT NULL, FOREIGN KEY(genre_id) REFERENCES genre(Id) ON UPDATE CASCADE ON DELETE CASCADE)')
                self.cursor.execute("CREATE TABLE genre(Id INTEGER PRIMARY KEY, genre VARCHAR(10) UNIQUE NOT NULL )")
                self.connect.commit()                
                database_version = '1.8.0'
        except sqlite3.OperationalError as e:
            logging.warn(e)
            self.cursor.execute("Select value from config where key='version'")
            row = self.cursor.fetchone()
            database_version = row[0]
            if database_version =='1.8.0':
                logging.info("Database is up to date")
                        
        
            
        
            
            
        


        
        
        
    



