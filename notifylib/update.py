import sqlite3
import logging
from notifylib.getmovies import Get_Movies
from notifylib.series import Series
from notifylib import util


class Update:
    def __init__(self, db_file):
        self.connect = sqlite3.connect(db_file)
        self.cursor = self.connect.cursor()

    def movie(self):
        movie = Get_Movies(self.cursor, self.connect)
        new_movie_list, movie_page = movie.fetch_new_movies()
        movie.insert_new_movies(new_movie_list, movie_page)

    def series(self):
        series = Series(self.cursor, self.connect)
        active_series = series.fetch_series_data()
        for series_info in active_series:
            try:
                all_episodes, new_ep_number, no_seasons = series.fetch_new_episdoes(series_info[1])
                if series_info[2] == 0:
                    series.new_series_episodes(all_episodes, new_ep_number,
                                               series_info[0], no_seasons)
                elif len(all_episodes) == series_info[2]:
                    logging.info("no new episodes for: %s", series_info[1])
                else:
                    new_episodes = util.series_compare(self.cursor, all_episodes,
                                                       series_info[0])
                    series.insert_new_epsiodes(new_episodes, new_ep_number,
                                                   series_info[0], no_seasons)
            except Exception as e:
                logging.info(e)
                continue

    def get_interval(self):
        self.cursor.execute("SELECT value FROM config WHERE key = 'update_interval'")
        time_int = self.cursor.fetchone()
        return time_int[0]

    def close(self):
        self.connect.close()


