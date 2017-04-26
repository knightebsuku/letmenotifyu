import webbrowser
import logging
import os
import requests

from urllib.request import Request, urlopen
from letmenotifyu import settings

log = logging.getLogger(__name__)


def render_view(image, string, store_model, image_file="ui/movies.png"):
    "Render GtkIconView"
    image.set_from_file(image_file)
    pixbuf = image.get_pixbuf()
    store_model.append([pixbuf, string])


def get_selection(view, store_model):
    "Get selection of GtkIconView"
    tree_path = view.get_selected_items()
    iters = store_model.get_iter(tree_path)
    model = view.get_model()
    selection = model.get_value(iters, 1)
    return selection


def open_page(cursor, title, option=None):
    "open webbrowser page"
    webbrowser.open_new("http://www.primewire.ag"+title)
    logging.info("Opening link {}".format(title))


def save_image(movie_link, meta):
    if os.path.isfile(settings.IMAGE_PATH+movie_link+".jpg"):
        pass
    else:
        log.debug("fetching image {}".format(movie_link))
        with open("%s" % (settings.IMAGE_PATH+movie_link+".jpg"), 'wb') as image_file:
            full_image_url = "http:"+meta['content']
            image_request = Request(full_image_url,
                          headers={'User-Agent': 'Mozilla/5.0'})
            image_file.write(urlopen(image_request).read())
            log.debug("Imaged fetched")


def start_logging():
    "Start logging"
    logging.basicConfig(filename=settings.LOG_FILE_PATH,
                            format='%(asctime)s - %(name)s-%(levelname)s:%(message)s', filemode='w',
                            level=settings.LOG_LEVEL)


def pre_populate_menu(builder):
    header_list = builder.get_object('HeaderList')
    header = header_list.append(None, ["Movies"])
    header_list.append(header, ["Released Movies"])
    header_list.append(header, ["Movie Archive"])
    header = header_list.append(None, ["Series"])
    header_list.append(header, ["Latest Episodes"])
    header_list.append(header, ["Series on Air"])
    header_list.append(header, ["Series Archive"])
    header = header_list.append(None, ['Watch Queue'])
    header_list.append(header, ["Movie Queue"])
    header_list.append(header, ["Series Queue"])


def fetch_torrent(torrent_url, title):
    "fetch torrent images"
    torrent_path = os.path.join(settings.TORRENT_DIRECTORY, title+".torrent")
    try:
        header = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0',}
        r = requests.get(torrent_url, headers=header)
        if r.status_code == requests.codes.ok:
            with open(torrent_path, "wb") as torrent_file:
                torrent_file.write(r.content)
                log.debug("torrent downloaded and saved")
                return True, torrent_path
        else:
            logging.debug("unable to download torrent {}".format(r.status_code))
            return False, None
    except requests.exceptions.ConnectionError as e:
            log.error("unable to fetch torrent for {}".format(title))
            log.exception(e)
            return False, None


def get_config_value(cursor, key):
    "get result from config table"
    cursor.execute("SELECT value FROM config WHERE key=?", (key,))
    (value,) = cursor.fetchone()
    return value
