#!/usr/bin/python3

import logging
import urllib
import requests
from . import util

log = logging.getLogger(__name__)


def get_released_movies(cursor):
    """
    Get list of movies released by yts and return json file
    """
    try:
        quality = util.get_config_value(cursor, "movie_quality")
        limit = util.get_config_value(cursor, 'max_movie_results')
        params = {'quality': quality, 'limit': limit.replace(".0", "")}
        data = requests.get("https://yts.ag/api/v2/list_movies.json",
                            params=params)
        log.debug(data.url)
        return data.json()
    except (urllib.error.URLError, urllib.error.HTTPError):
        logging.error("unable to connect to released movies api")
    except Exception as error:
        logging.exception(error)


def get_movie_details(yify_id):
    try:
        params = {'movie_id': yify_id}
        data = requests.get("https://yts.ag/api/v2/movie_details.json",
                            params=params)
        return data.json()
    except (urllib.error.URLError, urllib.error.HTTPError):
        logging.warn("Unable to connect to movie detail api")
    except Exception as error:
        logging.exception(error)
