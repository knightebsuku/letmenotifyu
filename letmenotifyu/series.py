#!/usr/bin/python3

from datetime import datetime
from letmenotifyu.notify import announce
from letmenotifyu import util
from letmenotifyu.primewire import primewire
import logging
import sqlite3


def fetch_new_episdoes(series_link):
    "search for new episodes"
    return primewire(series_link)


def series_compare(cursor, new_list, series_id):
    "Compare db list with new series"
    cursor.execute("SELECT episode_link from episodes where series_id=?",
                   (series_id,))
    data = [x[0] for x in cursor.fetchall()]
    new_data = [link for link in new_list if link[0] not in data]
    return new_data


def insert_records(connect, cursor, new_episodes, series_id, series_title):
    "inser new episodes"
    for (episode_link, episode_number, episode_name) in new_episodes:
        try:
            episode_row = cursor.execute("INSERT INTO episodes(" \
                                    'series_id,' \
                                    'episode_link,' \
                                    'episode_name,' \
                                    'episode_number,'\
                                    'Date) ' \
                                    'VALUES(?,?,?,?,?)'
                                    ,(series_id, episode_link, episode_name, episode_number, datetime.now(),))
            row_id = episode_row.lastrowid
            send_to_queue(series_id, episode_number, connect, row_id)
            connect.commit()
            announce("New Series Episode", series_title,
                         "www.primewire.ag" + episode_link)
        except sqlite3.IntegrityError:
            logging.error("Series episode {} already exists".format(episode_link))


def send_to_queue(series_id, episode_number, db, row_id):
    try:
        db.execute("INSERT INTO series_queue(series_id,episode_id, episode_name,watch_queue_status_id) "\
                   "VALUES(?,?,?,?)",(series_id, row_id, episode_number, 1,))
        logging.debug("episode {} added to series queue".format(episode_number))
    except sqlite3.IntegrityError:
        logging.warn("episode is already in the queue")


class Series(object):
    def __init__(self, connect, cursor):
        self.cursor = cursor
        self.connect = connect

    def update_series(self):
        self.cursor.execute('SELECT id,series_link,number_of_episodes from series where status=1')
        for (ids, series_link, number_eps,) in self.cursor.fetchall():
            try:
                series_info, episode_count, season_count = fetch_new_episdoes(series_link)
                if number_eps == 0:
                    logging.debug('series does not have any episodes, adding.....')
                    self.new_series_episodes(series_info, episode_count, ids, season_count)
                elif number_eps == episode_count:
                    logging.info("no new episodes for {}".format(series_link))
                elif number_eps < episode_count:
                    new_list = series_compare(self.cursor, series_info, ids)
                    self.insert_new_epsiodes(new_list, episode_count, ids, season_count)
            except TypeError:
                pass

    def insert_new_epsiodes(self, all_eps, new_ep_number, series_id, no_seasons):
        self.cursor.execute("SELECT title,watch from series where id=?", (series_id,))
        (series_detail, watch_status) = self.cursor.fetchone()
        if watch_status == 1:
            logging.debug('episodes will be added to watch list')
            insert_records(self.connect, self.cursor, all_eps, series_id, series_detail)
        else:
            for (episode_link, episode_number, episode_name) in all_eps:
                try:
                    self.cursor.execute("INSERT INTO episodes(" \
                                    'series_id,' \
                                    'episode_link,' \
                                    'episode_name,' \
                                    'episode_number,'\
                                    'Date) ' \
                                        'VALUES(?,?,?,?,?)'
                                    ,(series_id, episode_link, episode_name, episode_number, datetime.now(),))
                    self.connect.commit()
                    announce("New Series Episode", series_detail,
                             "www.primewire.ag" + episode_link)
                except sqlite3.IntegrityError:
                    logging.error("Series episode already exists")
        self.cursor.execute("UPDATE series set number_of_episodes=?,"\
                                'number_of_seasons=?,last_update=?  where id=?',
                                (new_ep_number, no_seasons, datetime.now(), series_id,))
        self.connect.commit()

    def new_series_episodes(self, all_episodes, new_ep_number, series_id, no_seasons):
        "new series"
        try:
            for (episode_link, episode_number, episode_name) in all_episodes:
                self.cursor.execute("INSERT INTO episodes("\
                                    'series_id,'\
                                    'episode_link,'\
                                    'episode_name,' \
                                    'episode_number) '\
                                    'VALUES(?,?,?,?)',
                                    (series_id, episode_link, episode_name, episode_number,))
            self.cursor.execute("UPDATE series set number_of_episodes=?,"\
                                'number_of_seasons=?,'\
                                'last_update=?,'\
                                'current_season=? '\
                                'where id=?',
                                 (new_ep_number, no_seasons, datetime.now(),
                                  no_seasons,  series_id,))
            util.series_poster(self.cursor, self.connect, series_id)
            self.connect.commit()
        except sqlite3.IntegrityError as e:
            logging.error("episode already exists")
            self.connect.rollback()
        except sqlite3.OperationalError as e:
            logging.exception(e)


def series(connect, cursor):
    "Initialise series to update"
    series_update = Series(connect, cursor)
    series_update.update_series()
