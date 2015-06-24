import logging
import webbrowser


class Torrent:
    def __init__(self, cursor):
        self.cursor = cursor

    def query(self, episode):
        self.cursor.execute('SELECT title FROM series WHERE id='\
                    '(SELECT series_id FROM episodes WHERE episode_name=?)', (episode,))
        self.title = self.cursor.fetchone()

    def kickass(self):
        self.cursor.execute("Select link  FROM torrent_sites WHERE name='Kickass'")
        result = self.cursor.fetchone()
        webbrowser.open_new(result[0]+self.title[0])
        logging.info("Opening kickass Link")
