import logging
import webbrowser



class Torrent:
    def __init__(self, cursor):
        self.cursor = cursor

    def query(self, episode):
        self.cursor.execute('SELECT title from series where id='+
                    '(SELECT series_id from episodes where episode_name=?)', (episode,))
        self.title = self.cursor.fetchone()

    def kickass(self):
        self.cursor.execute("Select link  from torrent_sites where name='Kickass'")
        result = self.cursor.fetchone()
        webbrowser.open_new(result[0]+self.title[0])
        logging.info("Opening kickass Link")
