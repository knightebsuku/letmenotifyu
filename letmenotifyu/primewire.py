#!/usr/bin/python3

import requests
import logging
import re

from bs4 import BeautifulSoup


def check_episode_numbers(episode_number):
    "check if episode numbers are valid"
    if 0 < int(episode_number) <= 26:
        return True


def check_season_number(season_number):
    "check if season number is valid"
    if int(season_number) > 0:
        return True


def modify_episode_number(season_value, episode_value):
    "format episode number"
    if int(season_value) < 10:
        season_value = "0{}".format(season_value)
    if int(episode_value) < 10:
        episode_value = "0{}".format(episode_value)
    return''.join(('S', season_value, 'E', episode_value))


def primewire(episode_site):
    "process series html page"
    try:
        series_page = requests.get(episode_site)
        series_page_data = BeautifulSoup(series_page.text)
        all_series_info = []
        for episode_item in series_page_data.find_all('div', {'class': 'tv_episode_item'}):
            link = episode_item.a['href']
            link_data = re.search(r'season-(\d+)-episode-(\d+)',link)
            if check_season_number(link_data.group(1)) and check_episode_numbers(link_data.group(2)):
                episode_number = modify_episode_number(link_data.group(1), link_data.group(2))
                ep_name = episode_item.find('a').contents[1].text
                all_series_info.append((link, episode_number, ep_name))
        seasons = series_page_data.find_all('a', {'class': 'season-toggle'})
        return all_series_info, len(all_series_info), len(seasons)
    except Exception as e:
        logging.warn("Unable to connect to {} ".format(episode_site))
        logging.exception(e)
