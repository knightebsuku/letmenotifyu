#!/usr/bin/python3

import transmissionrpc
import logging

logging.getLogger('transmissionrpc')


def check_episode_status(queue_id, cursor, db):
    "check the download status of particular episode"
    cursor.execute("SELECT torrent_hash FROM series_torrent_links WHERE series_queue_id=%s",
                   (queue_id,))
    (hash_id,) = cursor.fetchone()
    tc = transmissionrpc.Client('localhost', port='9091')
    for torrent in tc.get_torrents():
        if torrent.hashString == hash_id:
            if torrent.status == 'downloading':
                logging.debug("Updating episode with queue_id {} to  status 3".format(queue_id))
                cursor.execute("UPDATE series_queue set watch_queue_status_id=3 WHERE id=%s",
                               (queue_id,))
                db.commit()
            elif torrent.status == 'seeding':
                logging.info("Download complete for episode with queue_id {}".format(queue_id))
                cursor.execute("UPDATE series_queue set watch_queue_status_id=4 WHERE id=%s",
                               (queue_id,))
                db.commit()
            else:
                logging.debug("episode with queue_id is on status {}".format(torrent.status))


def check_movie_status(queue_id, cursor, db):
    "check download status of movies"
    cursor.execute("SELECT hash_sum from movie_torrent_links where movie_id=%s", (queue_id,))
    (hash_id,) = cursor.fetchone()
    tc = transmissionrpc.Client('localhost', port='9091')
    for torrent in tc.get_torrents():
        if torrent.hashString == hash_id:
            if torrent.status == 'downloading':
                logging.debug("Updating movie with queue_id {} to  status 3".format(queue_id))
                cursor.execute("UPDATE movie_queue set watch_queue_status_id=3 WHERE id=%s",
                               (queue_id,))
                db.commit()
            elif torrent.status == 'seeding':
                logging.info("Download complete for movie with queue_id {}".format(queue_id))
                cursor.execute("UPDATE movie_queue set watch_queue_status_id=4 WHERE id=%s",
                               (queue_id,))
                db.commit()
            else:
                logging.debug("movie with queue_id is on status {}".format(torrent.status))
