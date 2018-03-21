import transmissionrpc
import logging
import sqlite3
from . import util, settings

log = logging.getLogger(__name__)


def open_transmission():
    "connect to transmissionrpc"
    log.debug("connecting to transmission client")
    connect = sqlite3.connect(settings.GENERAL_DB)
    cursor = connect.cursor()
    cursor.execute(settings.SQLITE_WAL_MODE)
    host = util.get_config_value(cursor, 'transmission_host')
    port = util.get_config_value(cursor, 'transmission_port')
    log.debug("Host is {}".format(host))
    log.debug("port is {}".format(port))
    connect.close()
    return transmissionrpc.Client(host, port=port)


def add_torrent(torrent_file_path):
    "add torrent to transmission client"
    client = open_transmission()
    try:
        details = client.add_torrent(torrent_file_path)
        return details.hashString, details.name
    except transmissionrpc.error.TransmissionError:
        log.error("Unable to add torrent, fetch new torrent")
        raise NameError


def check_movie_status(watch_id, transmission_hash, cursor, db):
    try:
        client = open_transmission()
        torrent_status = client.get_torrent(transmission_hash)
        cursor.execute("SELECT mq.id FROM "
                       "movie_queue AS mq JOIN "
                       "movie_torrent_links AS mtl ON "
                       "mq.movie_id=mtl.movie_id AND "
                       "transmission_hash=?",
                       (transmission_hash,))
        (queue_id,) = cursor.fetchone()
        if torrent_status.status == 'downloading':
            log.debug("movie queue id {} to status 3".format(queue_id))
            cursor.execute("UPDATE movie_queue SET watch_queue_status_id=3 "
                           "WHERE id=?", (queue_id,))
            db.commit()
        elif torrent_status.isFinished:
            log.debug("movie queue Id {} to status 4".format(queue_id))
            cursor.execute("UPDATE movie_queue SET watch_queue_status_id=4 "
                           "WHERE id=?", (queue_id,))
            db.commit()
        elif torrent_status.status == 'seeding':
            log.debug("movie queue Id {} to status 4".format(queue_id))
            cursor.execute("UPDATE movie_queue SET watch_queue_status_id=4 "
                           "WHERE id=?", (queue_id,))
            db.commit()
    except KeyError as e:
        log.warn("unable to find movie torrent")
        raise KeyError
    except transmissionrpc.error.TransmissionError:
        log.error("unable to connect to transmissionrpc")
    except Exception as e:
        logging.exception(e)


def check_episode_status(watch_id, queue_id, cursor, db):
    "check status of episode download"
    try:
        cursor.execute("SELECT transmission_hash FROM series_torrent_links "
                       "WHERE series_queue_id=?", (queue_id,))
        (transmission_hash,) = cursor.fetchone()
        client = open_transmission()
        torrent_status = client.get_torrent(transmission_hash)
        if torrent_status.status == 'downloading':
            log.debug("series queue Id {} to status 3".format(queue_id))
            cursor.execute("UPDATE series_queue SET watch_queue_status_id=3 "
                           "WHERE id=?", (queue_id,))
            db.commit()
        elif torrent_status.isFinished:
            log.debug("series queue Id {} to status 4".format(queue_id))
            cursor.execute("UPDATE series_queue SET watch_queue_status_id=4 "
                           "WHERE id=?", (queue_id,))
            db.commit()
        elif torrent_status.status == 'seeding':
            log.debug("movie queue Id {} to status 4".format(queue_id))
            cursor.execute("UPDATE series_queue SET watch_queue_status_id=4 "
                           "WHERE id=?", (queue_id,))
            db.commit()
    except KeyError as e:
        log.warn("unable to find series torrent for {}".format(queue_id))
        raise KeyError
    except Exception as e:
        log.exception(e)
