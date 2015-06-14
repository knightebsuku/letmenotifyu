#!/usr/bin/python3

import logging
import json
import urllib
from urllib.request import urlopen
from . import util


def get_upcoming_movies():
    "Get list of upcoming movies by yifi"
    try:
        yifi_url = urlopen("https://yts.to/api/v2/list_upcoming.json")
        return json.loads(yifi_url.read().decode('utf-8'))
    except (urllib.error.URLError, urllib.error.HTTPError):
        logging.error("Unable to connect to upcoming movies api")
    except Exception as error:
        logging.exception(error)


def get_released_movies(cursor):
    "Get list of movies released by yifi"
    try:
        quality = util.get_config_value(cursor, "movie_quality")
        limit = util.get_config_value(cursor, 'max_movie_results')
        yifi_url = urlopen("https://yts.to/api/v2/list_movies.json?quality={}&limit={}".format(quality, limit))
        return json.loads(yifi_url.read().decode('utf-8'))
    except (urllib.error.URLError, urllib.error.HTTPError):
        logging.error("unable to connect to released movies api")
    except Exception as error:
        logging.exception(error)


def get_movie_details(yify_id):
    try:
        yify_url = urlopen("https://yts.to/api/v2/movie_details.json?movie_id={}&with_cast=true".format(yify_id))
        return json.loads(yify_url.read().decode('utf-8'))
    except (urllib.error.URLError, urllib.error.HTTPError):
        logging.warn("Unable to connect to movie detail api")
    except Exception as error:
        logging.exception(error)
