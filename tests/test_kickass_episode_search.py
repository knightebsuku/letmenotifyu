#!/usr/bin/python3

import requests
import re
import unittest
from bs4 import BeautifulSoup


class FetchTorrentTestCase(unittest.TestCase):
    def test_fetch_episode_search_results(self):
        "Search kickass page for episode"
        series_name = 'Falling Skies'
        episode_number = 'S05E03'
        kickass_url = 'https://kat.cr/usearch'
        search_url = "{url}/{title} {number} HDTV x264".format(url=kickass_url,
                                                 title=series_name,
                                                 number=episode_number)
        episode_results = requests.get(search_url)
        page_data = BeautifulSoup(episode_results.text)
        all_possible_results = page_data.find_all('tr', {'class': 'odd', 'class': 'even'})
        for results in all_possible_results:
            result_title = results.find('a', 'cellMainLink').text
            if re.match(r'{title} {episode_number} HDTV x264-(LOL|KILLERS|ASAP|2HD|FUM|TLA)'.format(title=series_name, episode_number=episode_number), result_title):
                for urls in results.find_all('a', 'icon16'):
                    if urls.get('title') == 'Download torrent file':
                        url = "OK"
                        torrent_url = urls.get('href')
                test_url = "OK"
                self.assertEqual(url, test_url)

if __name__ == "__main__":
    unittest.main()
