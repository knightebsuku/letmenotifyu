import requests
import logging

from bs4 import BeautifulSoup as Soup

MOVIE_URL = 'https://kat.cr/user/SaM/uploads/'
MOVIE_QUEUE = []


def get_movie_page():
    "Get list of movies from the 1st page"
    try:
        req = requests.get(MOVIE_URL)
        html_page = Soup(req.text, 'lxml')
        torrent_uploaded = html_page.find_all('tr',{'class':['odd', 'even']})
        for torrent in torrent_uploaded:
            movie_header = torrent.find('a', 'cellMainLink')
            title = movie_header.text
            url = movie_header['href']
            print(title)
            print(url)
            break
            
            
    except Exception as e:
        logging.INFO(e)
        

def insert_movie():
    "insert movie from queue"
