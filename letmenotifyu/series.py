import logging
import sqlite3
import json
import requests
import os


from typing import Dict
from datetime import datetime
from letmenotifyu.notify import announce
from . import settings, primewire
from requests.exceptions import ConnectionError, HTTPError

log = logging.getLogger(__name__)
Json = Dict[str, str]


class Series():
    "deal with series and episodes"
    def __init__(self):
        self.connect = sqlite3.connect(settings.SERIES_DB)
        self.cursor = self.connect.cursor()
        self.cursor.execute(settings.SQLITE_WAL_MODE)

    def update(self):
        "check for new episodes from primewire"
        self.cursor.execute("SELECT id,title,series_link,number_of_episodes "
                            "FROM series WHERE status='t'")
        for series_id, title, link, total_eps in self.cursor.fetchall():
            if total_eps == 0:
                log.info("new series, retriving all episodes")
                path = os.path.join(settings.IMAGE_PATH, title+'.jpg')
                details = json.loads(primewire.episodes(link))
                if self._poster(details['series_poster'],
                                title):
                    self._commit(details, series_id, path=path,
                                 notify=False, new=True)
            else:
                details = json.loads(primewire.episodes(link))
                self._commit(details, series_id, notify=True, new=False)

    def _commit(self, details, series_id, **kwargs):
        "Loop over episodes in json in insert"
        try:
            for episodes in details['episodes']:
                try:
                    self.cursor.execute("INSERT INTO episodes(series_id,"
                                        "episode_link,"
                                        "episode_name, episode_number, date) "
                                        "VALUES(?,?,?,?,?)",
                                        (series_id, episodes['episode_link'],
                                         episodes['episode_name'],
                                         episodes['episode_number'],
                                         datetime.now(),))
                    new_id = self.cursor.lastrowid
                    self.cursor.execute("INSERT INTO series_queue(series_id,"
                                        "episode_id,episode_name) VALUES(?,?,?)",
                                        (series_id, new_id,
                                         episodes['episode_name']))
                    self.connect.commit()
                    if kwargs['notify'] is True:
                        announce("New Series Episode",
                                 details['series_title'],
                                 episodes['episode_number'])
                except sqlite3.IntegrityError:
                    log.debug("episode already exists")
                except (sqlite3.OperationalError) as error:
                    log.error("unable to insert episode")
                    log.exception(error)
            if kwargs['new'] is True:
                self.cursor.execute("INSERT INTO series_images(series_id, path) "
                                    "VALUES(?,?)",
                                    (series_id, kwargs['path']))
            self.cursor.execute("UPDATE series SET number_of_episodes=?,"
                                'number_of_seasons=?,last_update=?,'
                                'current_season=? '
                                'WHERE id=?',
                                (details['total_episodes'],
                                 details['total_seasons'],
                                 datetime.now(),
                                 details['total_seasons'],
                                 series_id,))
            self.connect.commit()
        except sqlite3.IntegrityError:
            log.debug("episode already exists")
        except sqlite3.OperationalError as error:
            log.error("unable to insert episode")
            log.exception(error)
        finally:
            self.connect.close()

    def _poster(self, series_link, title):
        """
        Get series poster for newly added series
        """
        try:
            image_path = os.path.join(settings.IMAGE_PATH, title+".jpg")
            r = requests.get(series_link)
            if r.status_code == 200:
                with open(image_path, 'wb') as series_poster:
                    series_poster.write(r.content)
                log.info("series poster for {} downloaded".format(title))
                return True
        except(ConnectionError, HTTPError) as error:
            log.error("unable to download series poster")
            log.exception(error)
