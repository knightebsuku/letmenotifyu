#!/usr/bin/python3

import os
import configparser
import logging

DIRECTORY_PATH = os.path.join(os.environ['HOME'], '.letmenotifyu')
DATABASE_PATH = os.path.join(DIRECTORY_PATH, 'letmenotifyu.sqlite')
KICKASS_FILE = os.path.join(DIRECTORY_PATH, 'kickass.txt')
LOG_FILE_PATH = os.path.join(DIRECTORY_PATH, 'letmenotifyu.log')
DATA_FILES_PATH = '/usr/share/letmenotifyu/'
config = configparser.ConfigParser()


def logging_dict(log_level):
    levels = {'Logging.DEBUG': logging.DEBUG,
              'Logging.INFO': logging.INFO}
    return levels[log_level]


def create_ini_file():
    config['DIRECTORIES'] = {'ImagesDIrectory': os.path.join(DIRECTORY_PATH, 'images/'),
                             'TorrentsDirectory': os.path.join(DIRECTORY_PATH, 'torrents/'),
                             'CompleteDownloads': os.path.join(DIRECTORY_PATH, 'complete/'),
                             'IncompleteDownloads': os.path.join(DIRECTORY_PATH, 'incomplete/')}
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
except KeyError:
    os.mkdir(DIRECTORY_PATH)
    create_ini_file()
    TORRENT_DIRECTORY = config['DIRECTORIES']['TorrentsDirectory']
    IMAGE_PATH = config['DIRECTORIES']['ImagesDirectory']
    COMPLETE_DIRECTORY = config['DIRECTORIES']['CompleteDownloads']
    INCOMPLETE_DIRECTORY = config['DIRECTORIES']['IncompleteDownloads']
    LOG_LEVEL = logging_dict(config['LOGGING']['LoggingLevel'])
    os.mkdir(IMAGE_PATH)
    os.mkdir(TORRENT_DIRECTORY)
    os.mkdir(INCOMPLETE_DIRECTORY)
    os.mkdir(COMPLETE_DIRECTORY)
