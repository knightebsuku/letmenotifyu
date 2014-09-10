import logging
import webbrowser

class Torrent:
    def __init__(self, title, cursor):
        self.title = title
        self.cursor = cursor
        self.split_title = self.title.split("-")
    
    def kickass(self):
        self.cursor.execute("Select link  from torrents where name='Kickass'")
        result = self.cursor.fetchone()
        webbrowser.open_new(result[0]+self.split_title[0])
        logging.info("Opening kickass Link")

    def piratebay(self):
        self.cursor.execute("SELECT link FROM torrents where name='The Pirate Bay")
        result = self.cursor.fetchone()
        webbrowser.open_new(result[0]+self.split_title[0])
        logging.info("Opening Piratebay Link")

    def online(self, dic):
        webbrowser.open_new(dic[self.title])
        logging.info("Opening online video Link")

