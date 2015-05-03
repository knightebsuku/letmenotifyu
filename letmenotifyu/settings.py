#!/usr/bin/python3

import os
import configparser
import logging

DIRECTORY_PATH = os.getcwd()+"/data"
DATABASE_PATH = DIRECTORY_PATH+'/dev.sqlite'
KICKASS_FILE = DIRECTORY_PATH+'/kickass.txt'
LOG_FILE_PATH = DIRECTORY_PATH+'/dev.log'
config = configparser.ConfigParser()


def logging_dict(log_level):
    levels = {'Logging.DEBUG': logging.DEBUG,
              'Logging.INFO': logging.INFO}
    return levels[log_level]


def create_ini_file():
    config['DIRECTORIES'] = {'ImagesDIrectory': DIRECTORY_PATH+'/images/',
                             'TorrentsDirectory': DIRECTORY_PATH+'/torrents/',
                             'CompleteDownloads':DIRECTORY_PATH+'/complete/',
                             'IncompleteDownloads': DIRECTORY_PATH+'/incomplete/'
    }
    config['DATABASE'] = {'Host': 'localhost',
                          'Port': '5432',
                          'User': 'letmenotifyu',
                          'Password': 'letmenotifyu',
                          'Database': 'letmedev'
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
    DB_NAME = config['DATABASE']['Database']
    DB_HOST = config['DATABASE']['Host']
    DB_PORT = config['DATABASE']['Port']
    DB_USER = config['DATABASE']['User']
    DB_PASSWORD = config['DATABASE']['Password']
    os.mkdir(IMAGE_PATH)
    os.mkdir(TORRENT_DIRECTORY)
    os.mkdir(INCOMPLETE_DIRECTORY)
    os.mkdir(COMPLETE_DIRECTORY)
    
