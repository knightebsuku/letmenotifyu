#!/usr/bin/python3

import os
import configparser

DIRECTORY_PATH = os.environ['HOME']+'/.letmenotifyu'
DATABASE_PATH = DIRECTORY_PATH+'/letmenotifyu.sqlite'
KICKASS_FILE = DIRECTORY_PATH+'/kickass.txt'
LOG_FILE_PATH = DIRECTORY_PATH+'/letmenotifyu.log'
DATA_FILES_PATH = '/usr/share/letmenotifyu/'
config = configparser.ConfigParser()

def create_ini_file():
    config['DIRECTORIES'] = {'ImagesDIrectory': DIRECTORY_PATH+'/images/',
                             'TorrentsDirectory': DIRECTORY_PATH+'/torrents/',
                             'CompleteDownloads':DIRECTORY_PATH+'/complete/',
                             'IncompleteDownloads': DIRECTORY_PATH+'/incomplete/'}
    with open(DIRECTORY_PATH+'/config.ini','w') as cfg_file:
        config.write(cfg_file)
    


try:
    config.read(DIRECTORY_PATH+'/config.ini')
    TORRENT_DIRECTORY = config['DIRECTORIES']['TorrentsDirectory']
    IMAGE_PATH = config['DIRECTORIES']['ImagesDirectory']
    COMPLETE_DIRECTORY = config['DIRECTORIES']['CompleteDownloads']
    INCOMPLETE_DIRECTORY = config['DIRECTORIES']['IncompleteDownloads']
except KeyError:
    os.mkdir(DIRECTORY_PATH)
    create_ini_file()
    TORRENT_DIRECTORY = config['DIRECTORIES']['TorrentsDirectory']
    IMAGE_PATH = config['DIRECTORIES']['ImagesDirectory']
    COMPLETE_DIRECTORY = config['DIRECTORIES']['CompleteDownloads']
    INCOMPLETE_DIRECTORY = config['DIRECTORIES']['IncompleteDownloads']
    os.mkdir(IMAGE_PATH)
    os.mkdir(TORRENT_DIRECTORY)
    os.mkdir(INCOMPLETE_DIRECTORY)
    os.mkdir(COMPLETE_DIRECTORY)
    
