import sqlite3
import threading
import logging
from notifylib.update import Update
from notifylib import util


class RunUpdate(threading.Thread):
    def __init__(self, db_file):
        self.db_file = db_file
        threading.Thread.__init__(self)
        self.event = threading.Event()

    def run(self):
        while not self.event.is_set():
            update = Update(self.db_file)
            update.movie()
            update.series()
            interval = update.get_interval()
            update.close()
            self.event.wait(float(interval))

    def stop(self):
        self.event.set()


class FetchPosters(threading.Thread):
    def __init__(self, db):
        self.db = db
        threading.Thread.__init__(self)
        self.event = threading.Event()
        
    def run(self):
        logging.info("Starting thread to fetch movie posters")
        connect = sqlite3.connect(self.db)
        cursor = connect.cursor()
        util.fetch_movies(cursor, connect)

    def stop(self):
        self.event.set()
