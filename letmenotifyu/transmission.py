#!/usr/bin/python3

import transmissionrpc
import logging

logging.getLogger('transmissionrpc')


def add_torrent(torrent_file_path):
    "add torrent to transmission"
    client = transmissionrpc.Client('localhost', port='9091')
    details = client.add_torrent(torrent_file_path)
    return details.hashString, details.name


def check_movie_status(transmission_hash, cursor, db):
    try:
        tc = transmissionrpc.Client('localhost', port='9091')
        torrent_status = tc.get_torrent(transmission_hash)
        cursor.execute("SELECT mq.id FROM "\
                           "movie_queue AS mq JOIN "\
                           "movie_torrent_links AS mtl ON "\
                           "mq.movie_id=mtl.movie_id AND "\
                           "transmission_hash=%s",
                           (transmission_hash,))
        (queue_id,) = cursor.fetchone()
        if torrent_status.status == 'downloading':
            logging.debug("updating movie {} to status 3".format(queue_id))
            cursor.execute("UPDATE movie_queue SET watch_queue_status_id=3 " \
                                      "WHERE id=%s", (queue_id,))
            db.commit()
        elif torrent_status.isFinished:
            logging.debug("updating movie {} to status 4".format(queue_id))
            cursor.execute("UPDATE movie_queue SET watch_queue_status_id=4 " \
                                      "WHERE id=%s", (queue_id,))
            db.commit()
    except Exception as e:
        logging.exception(e)


def check_episode_status(queue_id, cursor, db):
    "check status of episode download"
    try:
        cursor.execute("SELECT transmission_hash FROM series_torrent_links "\
                       "WHERE series_queue_id=%s", (queue_id,))
        (transmission_hash,) = cursor.fetchone()
        tc = transmissionrpc.Client('localhost', port='9091')
        torrent_status = tc.get_torrent(transmission_hash)
        if torrent_status.status == 'downloading':
            logging.debug("updating {} to status 3".format(queue_id))
            cursor.execute("UPDATE series_queue SET watch_queue_status_id=3 "\
                                          "WHERE id=%s", (queue_id,))
            db.commit()
        elif torrent_status.isFinished:
            logging.debug("updating {} to status 4".format(queue_id))
            cursor.execute("UPDATE series_queue SET watch_queue_status_id=4 "\
                                          "WHERE id=%s", (queue_id,))
            db.commit()
    except KeyError as e:
        logging.warn("unable to find torrent for {}".format(queue_id))
    except Exception as e:
        logging.exception(e)
