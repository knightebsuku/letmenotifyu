#!/usr/bin/python3

import transmissionrpc
import logging
from . import util

logging.getLogger('transmissionrpc')


def open_transmission(cursor):
    "connect to transmissionrpc"
    host = util.get_config_value(cursor, 'transmission_host')
    port = util.get_config_value(cursor, 'transmission_port')
    return transmissionrpc.Client(host, port=port[:-2])


def add_torrent(torrent_file_path, cursor):
    "add torrent to transmission"
    client = open_transmission(cursor)
    details = client.add_torrent(torrent_file_path)
    return details.hashString, details.name


def check_movie_status(watch_id, transmission_hash, cursor, db):
    try:
        client = open_transmission(cursor)
        torrent_status = client.get_torrent(transmission_hash)
        cursor.execute("SELECT mq.id FROM "\
                           "movie_queue AS mq JOIN "\
                           "movie_torrent_links AS mtl ON "\
                           "mq.movie_id=mtl.movie_id AND "\
                           "transmission_hash=%s",
                           (transmission_hash,))
        (queue_id,) = cursor.fetchone()
        if watch_id == 2 and torrent_status.status == 'downloading':
            logging.debug("updating movie queue Id {} to status 3".format(queue_id))
            cursor.execute("UPDATE movie_queue SET watch_queue_status_id=3 " \
                                      "WHERE id=%s", (queue_id,))
            db.commit()
        elif watch_id == 3 and torrent_status.isFinished:
            logging.debug("updating movie queue Id {} to status 4".format(queue_id))
            cursor.execute("UPDATE movie_queue SET watch_queue_status_id=4 " \
                                      "WHERE id=%s", (queue_id,))
            db.commit()
    except KeyError as e:
        logging.warn("unable to find movie torrent for {}".format(queue_id))
    except Exception as e:
        logging.exception(e)


def check_episode_status(watch_id, queue_id, cursor, db):
    "check status of episode download"
    try:
        cursor.execute("SELECT transmission_hash FROM series_torrent_links "\
                       "WHERE series_queue_id=%s", (queue_id,))
        (transmission_hash,) = cursor.fetchone()
        client = open_transmission(cursor)
        torrent_status = client.get_torrent(transmission_hash)
        if watch_id == 2 and torrent_status.status == 'downloading':
            logging.debug("updating series queue Id {} to status 3".format(queue_id))
            cursor.execute("UPDATE series_queue SET watch_queue_status_id=3 "\
                                          "WHERE id=%s", (queue_id,))
            db.commit()
        elif watch_id == 3 and torrent_status.isFinished:
            logging.debug("updating series queue Id {} to status 4".format(queue_id))
            cursor.execute("UPDATE series_queue SET watch_queue_status_id=4 "\
                                          "WHERE id=%s", (queue_id,))
            db.commit()
    except KeyError as e:
        logging.warn("unable to find series torrent for {}".format(queue_id))
    except Exception as e:
        logging.exception(e)
