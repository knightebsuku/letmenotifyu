#!/usr/bin/python3

import sqlite3
import logging

class Database(object):
    def __init__(self, db):
        self.connect = sqlite3.connect(db)
        self.db = self.connect.cursor()
        
    def add_change(self, change_list):
        for change in change_list:
            self.db.execute("pragma user_version")
            version = self.db.fetchone()
            if int(version[0]) > change[0]:
                logging.error("database version is greater or equal to the new change version")
                exit()
            else:
                try:
                    self.connect.execute(change[1])
                    self.connect.execute("pragma user_version = ?", (change[0],))
                    self.connect.commit()
                except sqlite3.OperationalError as e:
                    logging.error("Unable to insert recored")
                    logging.exception(e)
                finally:
                    self.connect.close()
