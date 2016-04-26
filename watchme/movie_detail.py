import sqlite3
import asyncio
import aiohttp

from . import settings
from bs4 import BeautifulSoup as Soup
from random import randint
from Queue import Queue

MOVIE_DETAIL_QUEUE = Queue()

PRIMEWIRE_URL = 'http://www.primewire.ag'

def fetch_movie_detail():
    loop = asyncio.get_event_loop()
    client = aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'})
    conn = sqlite3.connect(settings.MOVIE_DB_PATH)
    c = conn.cursor()
    try:
        urls = poll_detail_queue(c)
        fetch_pages = [fetch_page(client, url, movie_id) for movie_id,url in urls]
        loop.run_until_complete(asyncio.wait(fetch_pages))
    except sqlite3.OperationalError:
        logging.info("unable to retrive movie detail records")
    except Exception:
        pass
    finally:
        loop.close()
        client.close()
        conn.close()
        print('complete')

def poll_detail_queue(c):
    "get movie details by polling detail queue table"
    try:
        c.execute("SELECT movie.id,url FROM movie JOIN detail_queue ON movie.id=movie_id WHERE detail_queue_status_id <> 2 limit 1")
        return c.fetchall()
    except:
        raise sqlite3.OperationalError


async def fetch_page(client, url, movie_id):
    "get web page and send to queue for processing"
    sleeping = randint(0,20)
    print("Going to sleep for {}".format(sleeping))
    await asyncio.sleep(sleeping)
    print("Getting web page for {}".format(url))
    async with client.get(PRIMEWIRE_URL+url) as resp:
        assert resp.status == 200
        await detail(resp.read())
        #MOVIE_DETAIL_QUEUE.put([movie_id, resp.read()])

async def detail(web_page_text):
    "extract movie detail"
    page = Soup(web_page_text, 'lxml')
    movie_info = page.find('div', {'class': 'movie_info'})
