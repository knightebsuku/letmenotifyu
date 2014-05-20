import logging
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import re


def primewire(title, episode_site, eps):
        try:
            req = Request(episode_site, headers={'User-Agent':'Mozilla/5.0'})
            data = urlopen(req).read().decode('ISO-8859-1')
            soup = BeautifulSoup(data)
            episode_page_data = soup
            all_series_info = []
            div_class = episode_page_data.find_all('div',{'class':'tv_episode_item'})
            if not div_class:
                logging.warn("Got Div Class of %s" % div_class)
            else:
                for links in div_class:
                    for series_links in links.find_all('a'):
                        all_series_info.append((series_links.get('href'),
                                                links.get_text().replace(" ","")))
                    seasons = episode_page_data.findAll("h2",
                                                        text=re.compile(r'^Season'))
                return all_series_info, len(all_series_info), title, eps, len(seasons)
        except Exception as e:
            logging.warn("Unable to connect to %s " % episode_site)
            logging.exception(e)
