#!/usr/bin/python3

import logging
import re
import requests

from bs4 import BeautifulSoup


def fetch_episode_search_results(series_name, episode_number):
    "Search kickass page for episode torrent link"
    kickass_url = 'https://kat.cr/usearch'
    search_url = "{url}/{title} {number} HDTV x264".format(url=kickass_url,
                                                 title=series_name,
                                                 number=episode_number)
    try:
        episode_results = requests.get(search_url)
        page_data = BeautifulSoup(episode_results.text)
        all_possible_results = page_data.find_all('tr', {'class': ['odd', 'even']})
        for results in all_possible_results:
            result_title = results.find('a', 'cellMainLink').text
            if re.search(r'{title} {episode_number} HDTV x264-(LOL|KILLERS|ASAP|2HD|FUM|TLA)'.format(title=series_name, episode_number=episode_number), result_title):
                for urls in results.find_all('a', 'icon16'):
                    if urls.get('title') == 'Download torrent file':
                        logging.debug("found torrent link for {}-{}".format(series_name, episode_number))
                        return urls.get('href')
    except requests.exceptions.ConnectionError as e:
        logging.debug("unable to get torrent url for {}-{}".format(series_name, episode_number))
        logging.exception(e)
