#!/usr/bin/python3

from datetime import datetime
from letmenotifyu.notify import announce
from letmenotifyu import util
from letmenotifyu.primewire import primewire
import logging
import psycopg2


class Series(object):
    "deal with series and episodes"
    def __init__(self, db, cursor):
        self.cursor = cursor
        self.db = db

    def _add_episodes(self, series_id, new_episodes,  series_title, init='current'):
        "add new episodes"
        for (episode_link, episode_number, episode_name,) in new_episodes:
            try:
                self.cursor.execute("INSERT INTO episodes(" \
                                    'series_id,' \
                                    'episode_link,' \
                                    'episode_name,' \
                                    'episode_number,'\
                                    'Date) ' \
                                    'VALUES(%s,%s,%s,%s,%s) RETURNING id'
                                    ,(series_id, episode_link, episode_name, episode_number, datetime.now(),))
                episode_id = self.cursor.fetchone()[0]
                self._send_to_queue(series_id, episode_id, episode_number)
                self.db.commit()
                if init == 'current':
                    announce("New Series Episode", series_title, episode_number)
            except psycopg2.IntegrityError:
                logging.error("episode already exists")

    def _send_to_queue(self, series_id, episode_id, episode_number ):
        "send new episodes to queue"
        self.cursor.execute("INSERT INTO series_queue(series_id,"\
                           "episode_id, episode_name) VALUES(%s,%s,%s)", (series_id,
                                                                            episode_id, episode_number,))
            
    def _get_new_episodes(self, series_link):
        "check for new episodes"
        return primewire(series_link)

    def _series_compare(self, series_id, new_episode_list):
        "compare current series list with new list"
        self.cursor.execute("SELECT episode_link FROM episodes WHERE series_id=%s",
                   (series_id,))
        data = [x[0] for x in self.cursor.fetchall()]
        new_data = [link for link in new_episode_list if link[0] not in data]
        return new_data

    def _update_series_details(self, episode_count, season_count, series_id):
        "update details for series"
        self.cursor.execute("UPDATE series SET number_of_episodes=%s,"\
                                'number_of_seasons=%s,last_update=%s  WHERE id=%s',
                                (episode_count, season_count, datetime.now(), series_id,))
        self.db.commit()
        
    def update(self):
        self.cursor.execute("SELECT id,title,series_link,number_of_episodes FROM series WHERE status='1'")
        for (series_id, series_title, series_link, current_ep_no) in self.cursor.fetchall():
            try:
                all_episodes, episode_count, season_count = self._get_new_episodes(series_link)
                if current_ep_no == 0:
                    logging.debug('series does not have any episodes, adding.....')
                    self._add_episodes(series_id, all_episodes, series_title, 'new')
                    self._update_series_details(episode_count, season_count, series_id)
                    util.series_poster(self.cursor, self.db, series_id)
                elif current_ep_no == episode_count:
                    logging.info("no new episodes for {}".format(series_link))
                elif current_ep_no < episode_count:
                    compared_list = self._series_compare(series_id,
                                                         all_episodes)
                    self._add_episodes(series_id, compared_list, series_title)
                    self._update_series_details(episode_count, season_count, series_id)
            except TypeError:
                pass

def series(connect, cursor):
    "Initialise series to update"
    update_series = Series(connect, cursor)
    update_series.update()
