from datetime import datetime
from notifylib.notify import announce
import logging
from notifylib.sites import primewire
import re


class Get_Series:
    def __init__(self, cursor, connect):
        self.cursor = cursor
        self.connect = connect

    def fetch_series_data(self):
        self.cursor.execute('SELECT title,series_link,number_of_episodes from series where status=1')
        return self.cursor.fetchall()

    def fetch_new_episdoes(self, title, link, eps):
        if re.search(r'primewire', link):
            return primewire(title, link, eps)
        else:
            logging.warn("Unable to find matching link for %s" % title)

    def insert_new_epsiodes(self, all_eps, new_ep_number, title, no_seasons):
        logging.info("adding new episodes")
        self.cursor.execute("BEGIN TRANSACTION")
        try:
            for new_data in all_eps:
                self.cursor.execute("INSERT INTO episodes(title,episode_link,episode_name,Date) VALUES(?,?,?,?)",(title, new_data[0], new_data[1], datetime.now(),))
                announce("New Series Episode", title, "www.primewire.ag" + new_data[0])
            self.cursor.execute("COMMIT")
            self.cursor.execute("UPDATE series set number_of_episodes=?,number_of_seasons=?,last_update=?  where title=?", (new_ep_number, no_seasons, datetime.now(), title,))
        except Exception as e:
            logging.error("Unable to add new episodes")
            logging.exception(e)
            self.cursor.execute("ROLLBACK")

    def new_series_episodes(self, all_episodes, new_ep_number, title, no_seasons):
        logging.info("adding new series epsiodes")
        self.cursor.execute("BEGIN TRANSACTION")
        try:
            for new_data in all_episodes:
                self.cursor.execute("INSERT INTO episodes(title,episode_link,episode_name) VALUES(?,?,?)",(title, new_data[0], new_data[1],))
            self.cursor.execute("COMMIT")
            self.cursor.execute("UPDATE series set number_of_episodes=?,number_of_seasons=?,last_update=?,current_season=?  where title=?", (new_ep_number, no_seasons, datetime.now(), no_seasons,  title,))
            logging.info("New series episodes added")
        except Exception as e:
            logging.error("unable to add series episodes")
            logging.exception(e)
            self.cursor.execute("ROLLBACK")
