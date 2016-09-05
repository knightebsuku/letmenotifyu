import logging
import re
import requests

from bs4 import BeautifulSoup


log = logging.getLogger(__name__)



PIRATE_BAY_URL = "https://thepiratebay.org/search"
HEADER = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0',}


def episode_magnet_link(series_name, episode_number):
    """
    Get Magnet link for matching series with episode number
    """
    search_query = "{url}/{title} {episode_number} HDTV x264/0/99/0".format(
        url=PIRATE_BAY_URL,
        title=series_name,
        episode_number=episode_number
    )
    try:
        log.info("Searching for series at {}".format(search_query))
        result = requests.get(search_query, headers=HEADER)
        soup = BeautifulSoup(result.text, 'lxml')

        table = soup.find('table')
        table_rows = table.findAll('tr')

        for row in table_rows:
            name = row.find('a', {'class': 'detLink'})
            log.info("Searching for episode for {title} {episode}".format(
                title=series_name,
                epsiode=episode_number
            ))
            if name:
                if re.search(r'{title}.{episode_number}.(PROPER |INTERNAL |WEB-DL )?HDTV.x264-(LOL|KILLERS|ASAP|2HD|FUM|TLA|BATV)'.format(
                        title=series_name.replace(" ", "."),
                        episode_number=episode_number),
                             name.string):
                    log.info("Found matching episiode")
                    log.info("searching for magnet")
                    link = row.find(title="Download this torrent using magnet")
                    magnet_link = link['href']
                    log.info("Magnet Link found")
                    return magnet_link
    except requests.exceptions.ConnectionError as e:
        log.warn("Unable to connect to piratebay")
        log.exception(e)
