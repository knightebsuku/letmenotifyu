#!/usr/bin/python3

import sqlite3
import logging
import datetime as dt

class Database(object):
    def __init__(self, db):
        self.connect = sqlite3.connect(db)
        self.db = self.connect.cursor()

    def initialise(self):
        try:
            self.connect.execute("CREATE TABLE migration("+
                             'id INTEGER PRIMARY KEY NOT NULL,'+
                             'version INTEGER UNIQUE NOT NULL,'+
                             'date TIMESTAMP NOT NULL)')
            self.db.execute("INSERT INTO migration(version,date) VALUES(0,?)",(dt.datetime.now(),))
            self.connect.commit()
            logging.debug("migration table created")
        except Exception as e:
            logging.exception(e)
            exit()
        finally:
            self.connect.close()

    def add_change(self, change_list):
        "Add new schema changes"
        try:
            for change in change_list:
                self.db.execute("SELECT id from migration where version=?", (change[0],))
                result = self.db.fetchone()
                self.db.execute("SELECT max(version) from migration")
                max_id = self.db.fetchone()
                if result:
                    logging.debug("database version change has already been applied")
                elif max_id[0] > change[0]:
                    logging.debug("new version change is smaller the lastest change..")
                else:
                    self.connect.execute(change[1])
                    self.connect.execute("INSERT INTO migration(version,date) VALUES(?,?)", (change[0],dt.datetime.now(),))
                    self.connect.commit()
                    logging.debug(change[1])
        except sqlite3.OperationalError as e:
            logging.error("unable to insert change {}".format(change[0]))
            logging.exception(e)
            exit()
        finally:
            self.connect.close()
