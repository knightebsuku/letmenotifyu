from datetime import datetime
from notifylib.notify import announce
from notifylib import util
import logging
import re
import sqlite3

def fetch_new_episdoes(series_link):
    return util.primewire(series_link)

def series_compare(cursor, new_list, series_id):
    "Compare db list with new series"
    cursor.execute("SELECT episode_link from episodes where series_id=?",
                   (series_id,))
    data = [x[0] for x in cursor.fetchall()]
    new_data = [link for link in new_list if link[0] not in data]
    return new_data

def insert_records_queue(connect, cursor,new_episodes, series_id, series_title):
    for new_data in new_episodes:
        try:
            episode_row = cursor.execute("INSERT INTO episodes(" +
                                    'series_id,' +
                                    'episode_link,' +
                                    'episode_name,' +
                                    'Date) ' +
                                    'VALUES(?,?,?,?)'
                                    ,(series_id, new_data[0], new_data[1], datetime.now(),))
            row_id = episode_row.lastrowid
            send_to_queue(series_id,new_data[0],connect, row_id)
            connect.commit()
            announce("New Series Episode", series_title,
                         "www.primewire.ag" + new_data[0])
        except sqlite3.IntegrityError:
            logging.error("Series episode already exists")

def send_to_queue(series_id, episode_link, db, row_id):
    "parse episode link to send to queue"
    p = re.compile("season-(\d+)-episode-(\d+)$")
    search = p.search(episode_link)
    season_number = search.group(1)
    episode_number = search.group(2)
    if int(season_number) < 10:
        season_number = "0{}".format(season_number)
    if int(episode_number) < 10:
        episode_number = "0{}".format(episode_number)
    try:
        db.execute("INSERT INTO series_queue(series_id,episode_id, episode_name,watch_queue_status_id) "+
                   "VALUES(?,?,?,?)" ,(series_id,row_id,"S{}E{}".format(season_number,episode_number),1,))
        logging.debug("episode {} added to series queue".format(episode_link))
    except sqlite3.IntegrityError:
        logging.warn("episode is already in the queue")

class Series(object):
    def __init__(self, connect,cursor):
        self.cursor = cursor
        self.connect = connect

    def update_series(self):
        self.cursor.execute('SELECT id,series_link,number_of_episodes from series where status=1')
        for current_series in self.cursor.fetchall():
            series_info, episode_count, season_count = fetch_new_episdoes(current_series[1])
            if current_series[2] == 0:
                logging.debug('series does not have any episodes, adding.....')
                self.new_series_episodes(series_info, episode_count,current_series[0],season_count)
            elif current_series[2] == episode_count:
                logging.info("no new episodes for {}".format(current_series[1]))
            elif current_series[2] < episode_count:
                new_list = series_compare(self.cursor, series_info, current_series[0])
                self.insert_new_epsiodes(new_list, episode_count, current_series[0], season_count)
            

    def insert_new_epsiodes(self, all_eps, new_ep_number, series_id, no_seasons):
        self.cursor.execute("SELECT title,watch from series where id=?", (series_id,))
        series_detail = self.cursor.fetchone()
        if series_detail[1] == 1:
            logging.debug('episodes will be added to watch list')
            insert_records_queue(self.connect,self.cursor,all_eps,series_id,series_detail[0])
        else:
            for new_data in all_eps:
                try:
                    self.cursor.execute("INSERT INTO episodes(" +
                                    'series_id,' +
                                    'episode_link,' +
                                    'episode_name,' +
                                    'Date) ' +
                                    'VALUES(?,?,?,?)'
                                    ,(series_id, new_data[0], new_data[1], datetime.now(),))
                    self.connect.commit()
                    announce("New Series Episode", series_detail[0],
                         "www.primewire.ag" + new_data[0])
                except sqlite3.IntegrityError:
                    logging.error("Series episode already exists")
        self.cursor.execute("UPDATE series set number_of_episodes=?,"+
                                'number_of_seasons=?,last_update=?  where id=?',
                                (new_ep_number, no_seasons, datetime.now(), series_id,))
        self.connect.commit()

    def new_series_episodes(self, all_episodes, new_ep_number, series_id, no_seasons):
        "new series"
        try:
            for new_data in all_episodes:
                self.cursor.execute("INSERT INTO episodes("+
                                    'series_id,'+
                                    'episode_link,'+
                                    'episode_name) ' +
                                    'VALUES(?,?,?)',
                                    (series_id, new_data[0], new_data[1],))
            self.cursor.execute("UPDATE series set number_of_episodes=?,"+
                                'number_of_seasons=?,'+
                                'last_update=?,'+
                                'current_season=? '+
                                'where id=?',
                                 (new_ep_number, no_seasons, datetime.now(),
                                  no_seasons,  series_id,))
            util.series_poster(self.cursor, self.connect, series_id)
            self.connect.commit()
            logging.info("new series has all episodes")
        except Exception as e:
            logging.error("unable to add series episodes")
            logging.exception(e)
            self.connect.rollback()











