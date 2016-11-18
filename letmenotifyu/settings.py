#!/usr/bin/python3

import os
import configparser
import logging
import psycopg2

# DIRECTORY_PATH = os.path.join(os.environ['HOME'], '.letmenotifyu')
DIRECTORY_PATH = 'DevLetme'
DATABSE_PATH = 'database'
MOVIE_DB = os.path.join(DATABSE_PATH, 'movie.db')
SERIES_DB = os.path.join(DATABSE_PATH, 'series.db')
LOG_FILE_PATH = os.path.join(DIRECTORY_PATH, 'letmenotifyu.log')
DATA_FILES_PATH = '/usr/share/letmenotifyu/'
IMAGE_PATH = os.path.join(DIRECTORY_PATH, 'images')
config = configparser.ConfigParser()


def logging_dict(log_level):
    levels = {'Logging.DEBUG': logging.DEBUG,
              'Logging.INFO': logging.INFO}
    return levels[log_level]


def create_ini_file():
    complete_directory = os.path.join(DIRECTORY_PATH, 'complete')
    incomplete_directory = os.path.join(DIRECTORY_PATH, 'incomplete')
    
    config['DIRECTORIES'] = {
                             'CompleteDownloads': complete_directory,
                             'IncompleteDownloads': incomplete_directory}
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
    COMPLETE_DIRECTORY = config['DIRECTORIES']['CompleteDownloads']
    INCOMPLETE_DIRECTORY = config['DIRECTORIES']['IncompleteDownloads']
    LOG_LEVEL = logging_dict(config['LOGGING']['LoggingLevel'])
    DB_NAME = config['DATABASE']['Database']
    DB_HOST = config['DATABASE']['Host']
    DB_PORT = config['DATABASE']['Port']
    DB_USER = config['DATABASE']['User']
    DB_PASSWORD = config['DATABASE']['Password']
    os.mkdir(IMAGE_PATH)
    os.mkdir(INCOMPLETE_DIRECTORY)
    os.mkdir(COMPLETE_DIRECTORY)
