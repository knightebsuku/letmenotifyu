#!/usr/bin/python3

import os
import configparser
import logging
import psycopg2

# DIRECTORY_PATH = os.path.join(os.environ['HOME'], '.letmenotifyu')
DIRECTORY_PATH = 'DevLetme'
KICKASS_FILE = os.path.join(DIRECTORY_PATH, 'kickass.txt')
LOG_FILE_PATH = os.path.join(DIRECTORY_PATH, 'letmenotifyu.log')
DATA_FILES_PATH = '/usr/share/letmenotifyu/'
config = configparser.ConfigParser()

Images_Directory = os.path.join(DIRECTORY_PATH, 'images')
Torrents_Directory = os.path.join(DIRECTORY_PATH, 'torrents')
Complete_Downloads_Directory = os.path.join(DIRECTORY_PATH, 'complete')
Incomplete_Downloads_Directory = os.path.join(DIRECTORY_PATH, 'incomplete')


def logging_dict(log_level):
    levels = {'Logging.DEBUG': logging.DEBUG,
              'Logging.INFO': logging.INFO}
    return levels[log_level]


def create_ini_file():
    config['DIRECTORIES'] = {'ImagesDirectory': Images_Directory,
                             'TorrentsDirectory': Torrents_Directory,
                             'CompleteDownloads': Complete_Downloads_Directory,
                             'IncompleteDownloads': Incomplete_Downloads_Directory}
    config['DATABASE'] = {'Host': '172.16.210.128',
                          'Port': '5432',
                          'User': 'letmenotifyu',
                          'Password': 'letmenotifyu',
                          'Database': 'letmenotifyu'}
    config["LOGGING"] = {'LoggingLevel': "Logging.INFO"}
    with open(DIRECTORY_PATH+'/config.ini', 'w') as cfg_file:
        config.write(cfg_file)


def check_db():
    try:
        connect = psycopg2.connect(host=DB_HOST,
                                   database=DB_NAME,
                                   port=DB_PORT,
                                   user=DB_USER,
                                   password=DB_PASSWORD)
        try:
            cursor = connect.cursor()
            cursor.execute("SELECT max(id) from migration")
        except Exception as e:
            logging.exception(e)
            return 'migration'
    except psycopg2.OperationalError as e:
        logging.exception(e)
        return 'connect'


try:
    config.read(DIRECTORY_PATH+'/config.ini')
    TORRENT_DIRECTORY = config['DIRECTORIES']['Torrents_Directory']
    IMAGE_PATH = config['DIRECTORIES']['Images_Directory']
    COMPLETE_DIRECTORY = config['DIRECTORIES']['Complete_Downloads_Directory']
    INCOMPLETE_DIRECTORY = config['DIRECTORIES']['Incomplete_Downloads_Directory']
    LOG_LEVEL = logging_dict(config['LOGGING']['LoggingLevel'])
    DB_NAME = config['DATABASE']['Database']
    DB_HOST = config['DATABASE']['Host']
    DB_PORT = config['DATABASE']['Port']
    DB_USER = config['DATABASE']['User']
    DB_PASSWORD = config['DATABASE']['Password']
except KeyError:
    os.mkdir(DIRECTORY_PATH)
    create_ini_file()
    TORRENT_DIRECTORY = config['DIRECTORIES']['Torrents_Directory']
    IMAGE_PATH = config['DIRECTORIES']['Images_Directory']
    COMPLETE_DIRECTORY = config['DIRECTORIES']['Complete_Downloads_Directory']
    INCOMPLETE_DIRECTORY = config['DIRECTORIES']['Incomplete_Downloads_Directory']
    LOG_LEVEL = logging_dict(config['LOGGING']['LoggingLevel'])
    DB_NAME = config['DATABASE']['Database']
    DB_HOST = config['DATABASE']['Host']
    DB_PORT = config['DATABASE']['Port']
    DB_USER = config['DATABASE']['User']
    DB_PASSWORD = config['DATABASE']['Password']
    os.mkdir(IMAGE_PATH)
    os.mkdir(TORRENT_DIRECTORY)
    os.mkdir(INCOMPLETE_DIRECTORY)
    os.mkdir(COMPLETE_DIRECTORY)
