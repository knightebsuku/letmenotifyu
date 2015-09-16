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

    def _add_episodes(self,series_id, new_episodes):
        "add new episodes"
        for (episode_link, episode_number, episode_name) in new_episodes:
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
                return episode_id
            except psycopg2.IntegrityError:
                logging.error("episode already exists")

    def _send_to_queue(self,series_id, episode_id ):
        "send new episodes to queue"
        try:
            self.cursor.execute("INSERT INTO series_queue(series_id,"\
                           "episode_id,"\
                           "episode_name,"\
                           "watch_queue_status_id) "\
                   "VALUES(%s,%s,%s,%s)",(series_id,
                                          row_id,
                                          episode_number,
                                          1,))
            logging.debug("episode {} added to series queue".format(episode_number))
        except psycopg2.IntegrityError:
            self.db.rollback()
            logging.warn("episode is already in the queue")
            
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

    def _update_series(self):
        self.cursor.execute("SELECT id,series_link,number_of_episodes FROM series WHERE status='1'")
        for (series_id, series_link, current_ep_no) in self.cursor.fetchall():
            try:
                all_episodes, episode_count, season_count = self._get_new_episodes(series_link)
                if current_ep_no == 0:
                    logging.debug('series does not have any episodes, adding.....')
                    self._add_episodes(series_id, all_episodes)
                elif number_eps == episode_count:
                    logging.info("no new episodes for {}".format(series_link))
                elif number_eps < episode_count:
                    new_list = series_compare(self.cursor, series_info, ids)
                    self.insert_new_epsiodes(new_list, episode_count, ids, season_count)
            except TypeError:
                pass
                
def insert_records(connect, cursor, new_episodes, series_id, series_title):
    "inser new episodes"
    for (episode_link, episode_number, episode_name) in new_episodes:
        try:
            cursor.execute("INSERT INTO episodes(" \
                                    'series_id,' \
                                    'episode_link,' \
                                    'episode_name,' \
                                    'episode_number,'\
                                    'Date) ' \
                                    'VALUES(%s,%s,%s,%s,%s) RETURNING id'
                                    ,(series_id, episode_link, episode_name, episode_number, datetime.now(),))
            row_id = cursor.fetchone()[0]
            send_to_queue(series_id, episode_number, connect, cursor, row_id)
            connect.commit()
            announce("New Series Episode", series_title,
                         "www.primewire.ag" + episode_link)
        except psycopg2.IntegrityError:
            connect.rollback()
            logging.error("Series episode {} already exists".format(episode_link))
        except psycopg2.OperationalError as e:
            connect.rollback()
            logging.exception(e)

class Series(object):
    def __init__(self, connect, cursor):
        self.cursor = cursor
        self.connect = connect


    def insert_new_epsiodes(self, all_eps, new_ep_number, series_id, no_seasons):
        self.cursor.execute("SELECT title,watch FROM series WHERE id=%s", (series_id,))
        (series_detail, watch_status) = self.cursor.fetchone()
        if watch_status == 1:
            logging.debug('episodes will be added to watch list')
            insert_records(self.connect, self.cursor, all_eps, series_id, series_detail)
            self.cursor.execute("UPDATE series SET number_of_episodes=%s,"\
                                'number_of_seasons=%s,last_update=%s  WHERE id=%s',
                                (new_ep_number, no_seasons, datetime.now(), series_id,))
            self.connect.commit()
        else:
            for (episode_link, episode_number, episode_name) in all_eps:
                try:
                    self.cursor.execute("INSERT INTO episodes(" \
                                    'series_id,' \
                                    'episode_link,' \
                                    'episode_name,' \
                                    'episode_number,'\
                                    'date) ' \
                                        'VALUES(%s,%s,%s,%s,%s)'
                                    ,(series_id, episode_link, episode_name, episode_number, datetime.now(),))
                    self.cursor.execute("UPDATE series SET number_of_episodes=%s,"\
                                'number_of_seasons=%s,last_update=%s  WHERE id=%s',
                                (new_ep_number, no_seasons, datetime.now(), series_id,))
                    self.connect.commit()
                    announce("New Series Episode", series_detail,
                             "www.primewire.ag" + episode_link)
                except psycopg2.IntegrityError:
                    self.connect.rollback()
                    logging.error("Series episode already exists")
                except psycopg2.OperationalError as e:
                    self.connect.rollback()
                    logging.exception(e)

    def new_series_episodes(self, all_episodes, new_ep_number, series_id, no_seasons):
        "new series"
        try:
            for (episode_link, episode_number, episode_name) in all_episodes:
                self.cursor.execute("INSERT INTO episodes("\
                                    'series_id,'\
                                    'episode_link,'\
                                    'episode_name,' \
                                    'episode_number) '\
                                    'VALUES(%s,%s,%s,%s)',
                                    (series_id, episode_link, episode_name, episode_number,))
            self.cursor.execute("UPDATE series SET number_of_episodes=%s,"\
                                'number_of_seasons=%s,'\
                                'last_update=%s,'\
                                'current_season=%s '\
                                'WHERE id=%s',
                                 (new_ep_number, no_seasons, datetime.now(),
                                  no_seasons,  series_id,))
            util.series_poster(self.cursor, self.connect, series_id)
            self.connect.commit()
        except psycopg2.IntegrityError as e:
            self.connect.rollback()
            logging.error("episode already exists")
        except psycopg2.OperationalError as e:
            self.connect.rollback()
            logging.exception(e)


def series(connect, cursor):
    "Initialise series to update"
    series_update = Series(connect, cursor)
    series_update.update_series()
