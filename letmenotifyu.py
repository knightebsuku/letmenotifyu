#!/usr/bin/python3

import os
import logging
from notifylib import database as db
from notifylib.main import Main
from notifylib import settings
from notifylib import util

if __name__ == "__main__":
    if not os.path.isdir(settings.DIRECTORY_PATH):
        util.initialise()
    util.start_logging()
    if  not os.path.isfile(settings.DATABASE_PATH):
        logging.info("no database file found")
        db.database_init()
    db.database_change()
    Main()
