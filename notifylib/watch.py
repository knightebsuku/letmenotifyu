#!/usr/bin/python3

import re
import sqlite3
import logging



def send_to_queue(series_id, episode_link, db):
    "send new episode to queue"
    p = re.compile("season-(\d+)-episode-(\d+)$")
    search = p.search(episode_link)
    season_number = search.group(1)
    episode_number = search.group(2)
    try:
        db.execute("INSERT INTO watch_queue(series_id,episode_name,watch_status_id) "+
               "VALUES(?,?,?)" ,(series_id,"s{}e{}".format(season_number,episode_number),1,))
        db.commit()
    except sqlite3.IntegrityError:
        logging.warn("episode is already in the queue")


def process_queue(db):
    "process episodes in the watch queue"
    logging.debug("checking for new episodes")
    db.execute("SELECT title,episode_name from watch_queue join series on "+
               "series.id=watch_queue.series_id and watch_status_id=1")
    if not db.fetchall():
        logging.debug("no new episodes")
    else:
        logging.debug("new episodes to process")
        
