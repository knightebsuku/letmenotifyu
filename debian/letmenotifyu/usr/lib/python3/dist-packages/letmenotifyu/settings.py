#!/usr/bin/python3

import os
import configparser

DIRECTORY_PATH = os.environ['HOME']+'/.letmenotifyu'
config = configparser.ConfigParser()

def create_ini_file():
    config['DIRECTORIES'] = {'ImagesDIrectory': DIRECTORY_PATH+'/images/',
                             'TorrentsDirectory': DIRECTORY_PATH+'/torrents/',
                             'CompleteDownloads':DIRECTORY_PATH+'/complete/',
                             'IncompleteDownloads': DIRECTORY_PATH+'/incomplete/'}
    with open(DIRECTORY_PATH+'/config.ini','w') as cfg_file:
        config.write(cfg_file)
    
DATABASE_PATH = DIRECTORY_PATH+'/letmenotifyu.sqlite'
KICKASS_FILE = DIRECTORY_PATH+'/kickass.txt'
LOG_FILE_PATH = DIRECTORY_PATH+'/letmenotifyu.log'
ICON_FILE_PATH = DIRECTORY_PATH+'/icons/'
DATA_FILES_PATH = '/usr/share/letmenotifyu/'

try:
    config.read(DIRECTORY_PATH+'/config.ini')
    TORRENT_DIRECTORY = config['DIRECTORIES']['TorrentsDirectory']
    IMAGE_PATH = config['DIRECTORIES']['ImagesDirectory']
    COMPLETE_DIRECTORY = config['DIRECTORIES']['CompleteDownloads']
    INCOMPLETE_DIRECTORY = config['DIRECTORIES']['IncompleteDownloads']
except KeyError:
    create_ini_file()
