import logging
import requests
import sqlite3
from typing import Dict, List
from . import util, settings
from requests.exceptions import ConnectionError, HTTPError

log = logging.getLogger(__name__)

Json = Dict[str, str]


def new_movies() -> List[Json]:
    """
    Get list of movies released by yts and return json file
    """
    connect = sqlite3.connect(settings.MOVIE_DB)
    cursor = connect.cursor()
    try:
        quality = util.get_config_value(cursor, "movie_quality")
        limit = util.get_config_value(cursor, 'max_movie_results')
        params = {'quality': quality, 'limit': limit.replace(".0", "")}
        data = requests.get("https://yts.ag/api/v2/list_movies.json",
                            params=params)
        return data.json()
    except (ConnectionError, HTTPError) as e:
        logging.error("unable to connect to released movies api")
        log.error(e)
        raise
    except Exception as error:
        log.error("Unknow exception")
        logging.exception(error)
        raise
    finally:
        connect.close()


def movie_details(yify_id: str) -> Json:
    try:
        params = {'movie_id': yify_id}
        data = requests.get("https://yts.ag/api/v2/movie_details.json",
                            params=params)
        return data.json()
    except (ConnectionError, HTTPError) as error:
        log.warn("Unable to connect to yify movie details api")
        log.exception(error)
