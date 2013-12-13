
import sqlite3
from datetime import datetime

class Database:
    def __init__(self,db_file):
        self.db_file=db_file
        self.connect=sqlite3.connect(self.db_file)
        self.cursor=self.connect.cursor()
        
    def create_database(self):
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.cursor.execute('CREATE TABLE movies(id INTEGER PRIMARY KEY, title VARCHAR(20), link VARCHAR(20))')
        self.cursor.execute('CREATE TABLE series(title VARCHAR(30) PRIMARY KEY,series_link VARCHAR(60),number_of_episodes INTEGER,number_of_seasons INTEGER,last_update TIMESTAMP,status BOOLEAN)')
        self.cursor.execute('CREATE TABLE episodes(id INTEGER PRIMARY KEY,title VARCHAR(30),episode_name VARCHAR(15), episode_link VARCHAR(40), Date TIMESTAMP, FOREIGN KEY (title) REFERENCES series(title) ON DELETE CASCADE)')
        self.cursor.execute('CREATE TABLE schema_version(id IINTEGER PRIMARY KEY,version VARCHAR(6))')
        self.cursor.execute('INSERT INTO schema_version(version) VALUES ("1.7.2")')
        self.connect.commit()
        self.connect.close()

    def upgrade_database(self):
        self.cursor.execute("SELECT version FROM schema_version")
        row=self.cursor.fetchone()
        database_version= row[0]
        if database_version=='1.7.2':
            print("Upgrading to version 1.7.3")
            self.cursor.execute("CREATE TABLE torrents(Id INTEGER PRIMARY KEY,name VARCHAR(20),link VARCHAR(20))")
            self.cursor.execute("INSERT INTO torrents(name) VALUES('http://kickass.to/usearch/')")
            self.connect.commit()
            self.cursor.execute("INSERT INTO torrents(name) VALUES('http://thepiratebay.sx/search/')")
            self.connect.commit()
            self.cursor.execute("INSERT INTO torrents(name) VALUES('http://isohunt.to/torrents/?ihq=')")
            self.connect.commit()
            self.cursor.execute("UPDATE schema_version set version='1.7.3' where id=1")
            self.connect.commit()
            database_version='1.7.3'
            
        if database_version=='1.7.3':
            print("need to upgrade to 1.8.0")
            self.cursor.execute('DROP table schema_verison')
            self.cursor.execute('CREATE TABLE schema_version(version VARCHAR(6))')
            self.cursor.execute("UPDATE schema_version set version='1.8.0'")
            self.connect.commit()
            
            
        


        
        
        
    
