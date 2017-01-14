import logging
import re
import requests

from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

def fetch_episode_search_results(series_name, episode_number):
    "Search kickass page for episode torrent link"
    kickass_url = 'https://kickass.cd/search.php?q='
    search_url = "{url}{title} {number} HDTV x264".format(url=kickass_url,
                                                          title=series_name,
                                                          number=episode_number)
    try:
        header = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0',}
        episode_results = requests.get(search_url, headers=header)
        page_data = BeautifulSoup(episode_results.text, "lxml")
        all_possible_results = page_data.find_all('tr',
                                                  {'class': ['odd', 'even']})
        for results in all_possible_results:
            result_title = results.find('a', 'cellMainLink').text
            new_title_name = series_name.replace(" ", ".")
            log.debug("Search results %s", result_title)
            if re.search(r'{title}.{episode_number}.(PROPER.|INTERNAL.|WEB-DL.)?HDTV.x264-(LOL|KILLERS|ASAP|2HD|FUM|TLA|BATV|FLEET)'.format(title=new_title_name, episode_number=episode_number), result_title):
                for urls in results.find_all('a', 'icon16'):
                    if urls.get('title') == 'Torrent magnet link':
                        log.debug("found magnet link for {}-{}".format(series_name, episode_number))
                        log.debug(urls.get('href'))
                        return urls.get('href')
                    else:
                        log.info("Unable to find torrent magnet link")
            else:
                print(re.DEBUG)
                log.info("Unable to find search title {} on kickass.cd".format(search_url))
    except requests.exceptions.ConnectionError as error:
        log.debug("unable to connect to kickass.cd for {}-{}".format(series_name,
                                                               episode_number))
        log.exception(error)
