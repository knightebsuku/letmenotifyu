
import sqlite3
import logging

logging.getLogger(__name__)

class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.connect = sqlite3.connect(self.db_file)
        self.cursor = self.connect.cursor()
        
    def create_database(self):
        logging.info("Creating new Database")
        self.cursor.execute("PRAGMA foreign_keys = ON")
        logging.info("****Creating table Genre****")
        self.cursor.execute("CREATE TABLE genre(Id INTEGER PRIMARY KEY, genre VARCHAR(10) UNIQUE NOT NULL )")
        logging.info("****Creating movie table****")
        self.cursor.execute('CREATE TABLE movies(Id INTEGER PRIMARY KEY, genre_id INTEGER  NOT NULL, title VARCHAR(20) UNIQUE NOT NULL, link VARCHAR(20) NOT NULL, FOREIGN KEY(genre_id) REFERENCES genre(Id) ON UPDATE CASCADE ON DELETE CASCADE)')
        logging.info("****Creating series table****")
        self.cursor.execute('CREATE TABLE series(title VARCHAR(30) PRIMARY KEY,series_link VARCHAR(60),number_of_episodes INTEGER,number_of_seasons INTEGER,current_season INTEGER,last_update TIMESTAMP,status BOOLEAN)')
        logging.info("****Creating episodes table****")
        self.cursor.execute('CREATE TABLE episodes(id INTEGER PRIMARY KEY,title VARCHAR(30) NOT NULL,episode_name VARCHAR(15) NOT NULL, episode_link VARCHAR(40) NOT NULL, Date TIMESTAMP NOT NULL, FOREIGN KEY (title) REFERENCES series(title) ON DELETE CASCADE)')
        self.connect.commit()
        self.cursor.execute("CREATE TABLE config(id INTEGER PRIMARY KEY, key VARCHAR(20) NOT NULL, value VARCHAR(20) NOT NULL)")
        self.connect.commit()
        self.cursor.execute("INSERT INTO config(key,value) VALUES('update_interval','3600')")
        self.connect.commit()
        self.cursor.execute("CREATE TABLE torrents(Id INTEGER PRIMARY KEY,name VARCHAR(20) NOT NULL,link VARCHAR(20) NOT NULL)")
        logging.info("****Inserting default records****")
        self.cursor.execute("INSERT INTO torrents(name,link) VALUES('Kickass','http://kickass.to/usearch/')")
        self.connect.commit()
        self.cursor.execute("INSERT INTO torrents(name,link) VALUES('The Pirate Bay','http://thepiratebay.sx/search/')")
        self.connect.commit()
        self.cursor.execute("INSERT INTO torrents(name,link) VALUES('Isohunt','http://isohunt.to/torrents/?ihq=')")
        self.connect.commit()
        self.cursor.execute("INSERT INTO config(key,value) VALUES('movie_directory','0')")
        self.connect.commit()
        self.cursor.execute("INSERT INTO config(key,value) VALUES('series_directory','0')")
        self.connect.commit()
        self.cursor.execute("UPDATE config SET value='1.9.0' WHERE key='version'")
        self.connect.commit()
        logging.info("Database has been created")

    def upgrade_database(self):
        self.cursor.execute("SELECT value FROM config WHERE key='version'")
        version = self.cursor.fetchone()
        database_version = version[0]

        if database_version == '1.8.0':
            logging.info("****Database is being upgraded to version 1.9.0****")
            logging.warn("Dropping table torrents and recreating it.")
            self.cursor.execute("DROP TABLE torrents")
            self.cursor.execute("CREATE TABLE torrents(Id INTEGER PRIMARY KEY NOT NULL,name VARCHAR(20) NOT NULL,link VARCHAR(20) NOT NULL)")
            self.cursor.execute("INSERT INTO torrents(name,link) VALUES('Kickass','http://kickass.to/usearch/')")
            self.connect.commit()
            self.cursor.execute("INSERT INTO torrents(name,link) VALUES('The Pirate Bay','http://thepiratebay.sx/search/')")
            self.connect.commit()
            self.cursor.execute("INSERT INTO torrents(name,link) VALUES('Isohunt','http://isohunt.to/torrents/?ihq=')")
            self.connect.commit()
            logging.info("Inserting new config values ")
            self.cursor.execute("INSERT INTO config(key,value) VALUES('movie_directory','0')")
            self.connect.commit()
            self.cursor.execute("INSERT INTO config(key,value) VALUES('series_directory','0')")
            self.connect.commit()

            self.cursor.execute("UPDATE config SET value='1.9.0' WHERE key='version'")
            self.connect.commit()
            logging.info("Database has being upgraded to version 1.9.0")
            database_version = '1.9.0'


        if database_version =='1.9.0':
            logging.warn("Need to update the database to version 1.9.2")
            logging.warn("***Starting upgrade***")
            #self.cursor.execute("alter table series add current_season INTEGER")
            #self.connect.commit()
            self.cursor.execute("CREATE TABLE series_source(Id INTEGER PRIMARY KEY,name  VARCHAR NOT NULL)")
            logging.info("Database upgrade has being completed")
            self.cursor.execute("UPDATE config set value='1.9.2' where key='version'")


            
            
            
        
            
            
        
            
            
        


        
        
        
    






