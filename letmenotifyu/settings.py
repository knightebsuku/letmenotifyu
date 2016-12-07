#!/usr/bin/python3

import os
import configparser
import logging
import psycopg2

log = logging.getLogger(__name__)

# DIRECTORY_PATH = os.path.join(os.environ['HOME'], '.letmenotifyu')
DIRECTORY_PATH = 'DevLetme'
DATABSE_PATH = os.path.join(DIRECTORY_PATH, 'database')
MOVIE_DB = os.path.join(DATABSE_PATH, 'movie.db')
SERIES_DB = os.path.join(DATABSE_PATH, 'series.db')
LOG_FILE_PATH = os.path.join(DIRECTORY_PATH, 'letmenotifyu.log')
#DATA_FILES_PATH = '/usr/share/letmenotifyu/'
IMAGE_PATH = os.path.relpath(os.path.join(DIRECTORY_PATH, 'images'))
SQLITE_WAL_MODE = "PRAGMA journal_mode=WAL"
config = configparser.ConfigParser()


def logging_dict(log_level):
    levels = {'Logging.DEBUG': logging.DEBUG,
              'Logging.INFO': logging.INFO}
    return levels[log_level]


def create_ini_file():
    """
    Create config file upon install start of application
    """
    config['DIRECTORIES'] = {'CompleteDownloads': os.path.join(DIRECTORY_PATH, 'complete'),
                             'IncompleteDownloads': os.path.join(DIRECTORY_PATH, 'incomplete')}
    config["LOGGING"] = {'LoggingLevel': "Logging.INFO"}
    with open(DIRECTORY_PATH+'/config.ini', 'w') as cfg_file:
        config.write(cfg_file)


def check_db():
    if os.path.exists(MOVIE_DB) and os.path.exists(SERIES_DB):
        return True
    else:
        log.error("movie or series database do not exist")
        raise ValueError("movie or series database not found")

try:
    config.read(DIRECTORY_PATH+'/config.ini')
    COMPLETE_DIRECTORY = config['DIRECTORIES']['CompleteDownloads']
    INCOMPLETE_DIRECTORY = config['DIRECTORIES']['IncompleteDownloads']
    LOG_LEVEL = logging_dict(config['LOGGING']['LoggingLevel'])
except KeyError:
    os.mkdir(DIRECTORY_PATH)
    os.mkdir(IMAGE_PATH)
    os.mkdir(DATABSE_PATH)
    create_ini_file()
    COMPLETE_DIRECTORY = config['DIRECTORIES']['CompleteDownloads']
    INCOMPLETE_DIRECTORY = config['DIRECTORIES']['IncompleteDownloads']
    LOG_LEVEL = logging_dict(config['LOGGING']['LoggingLevel'])
    os.mkdir(INCOMPLETE_DIRECTORY)
    os.mkdir(COMPLETE_DIRECTORY)
