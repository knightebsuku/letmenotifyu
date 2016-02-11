#!/usr/bin/python3

import os
import configparser
import logging
import psycopg2

from . import database

#DIRECTORY_PATH = os.path.join(os.environ['HOME'], '.letmenotifyu')
DIRECTORY_PATH = os.path.join("letme4")
DATABASE_PATH = os.path.join(DIRECTORY_PATH, 'database')
IMAGE_DIRECTORY = os.path.join(DIRECTORY_PATH, 'images')
TORRENT_DIRECTORY = os.path.join(DIRECTORY_PATH, 'torrents')
INCOMPLETE_DIRECTORY = os.path.join(DIRECTORY_PATH, 'incomplete')
COMPLETE_DIRECTORY = os.path.join(DIRECTORY_PATH, 'complete')
LOG_FILE_PATH = os.path.join(DIRECTORY_PATH, 'letmenotifyu.log')
#DATA_FILES_PATH = '/usr/share/letmenotifyu/'

config = configparser.ConfigParser()


def database_exsist(db_name):
    return os.path.isfile(DATABASE_PATH+db_name)
                          
def logging_dict(log_level):
    levels = {'Logging.DEBUG': logging.DEBUG,
              'Logging.INFO': logging.INFO}
    return levels[log_level]


def initial():
    os.mkdir(IMAGE_PATH)
    os.mkdir(TORRENT_DIRECTORY)
    os.mkdir(INCOMPLETE_DIRECTORY)
    os.mkdir(COMPLETE_DIRECTORY)
    config['DIRECTORIES'] = {'ImagesDirectory': DIRECTORY_PATH+'/images/',
                             'TorrentsDirectory': DIRECTORY_PATH+'/torrents/',
                             'CompleteDownloads':DIRECTORY_PATH+'/complete/',
                             'IncompleteDownloads': DIRECTORY_PATH+'/incomplete/'
    }
    config["LOGGING"] = {'LoggingLevel': "Logging.INFO"}
    with open(DIRECTORY_PATH+'/config.ini','w') as cfg_file:
        config.write(cfg_file)



try:
    config.read(DIRECTORY_PATH+'/config.ini')
    TORRENT_DIRECTORY = config['DIRECTORIES']['TorrentsDirectory']
    IMAGE_PATH = config['DIRECTORIES']['ImagesDirectory']
    COMPLETE_DIRECTORY = config['DIRECTORIES']['CompleteDownloads']
    INCOMPLETE_DIRECTORY = config['DIRECTORIES']['IncompleteDownloads']
    LOG_LEVEL = logging_dict(config['LOGGING']['LoggingLevel'])
    DB_NAME = config['DATABASE']['Database']
    DB_HOST = config['DATABASE']['Host']
    DB_PORT = config['DATABASE']['Port']
    DB_USER = config['DATABASE']['User']
    DB_PASSWORD = config['DATABASE']['Password']
except KeyError:
    os.mkdir(DIRECTORY_PATH)
    create_ini_file()
    TORRENT_DIRECTORY = config['DIRECTORIES']['TorrentsDirectory']
    IMAGE_PATH = config['DIRECTORIES']['ImagesDirectory']
    COMPLETE_DIRECTORY = config['DIRECTORIES']['CompleteDownloads']
    INCOMPLETE_DIRECTORY = config['DIRECTORIES']['IncompleteDownloads']
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
    
