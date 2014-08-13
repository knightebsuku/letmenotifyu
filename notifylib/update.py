import sqlite3
import logging
from notifylib.getmovies import Get_Movies
from notifylib.getseries import Get_Series


class Update:
    def __init__(self, db_file):
        self.connect = sqlite3.connect(db_file)
        self.cursor = self.connect.cursor()

    def movie(self):
        movie = Get_Movies(self.cursor, self.connect)
        new_movie_list, movie_page = movie.fetch_new_movies()
        movie.insert_new_movies(new_movie_list, movie_page)

    def series(self):
        series = Get_Series(self.cursor, self.connect)
        all_series = series.fetch_series_data()
        for data in all_series:
            try:
                all_episodes, new_ep_number, title, current_ep_number, no_seasons = series.fetch_new_episdoes(data[0], data[1], data[2])
                if current_ep_number == 0:
                    series.new_series_episodes(all_episodes, new_ep_number, title, no_seasons)
                elif len(all_episodes) == current_ep_number:
                    logging.info("no new episodes for: %s", data[1])
                else:
                    new_episodes = compare(self.cursor, all_episodes, title)
                    series.insert_new_epsiodes(new_episodes, new_ep_number,
                                                   title, no_seasons)
            except Exception as e:
                logging.info(e)
                continue

    def get_interval(self):
        self.cursor.execute("SELECT value FROM config WHERE key = 'update_interval'")
        time_int = self.cursor.fetchone()
        return time_int[0]

    def close(self):
        self.connect.close()


def compare(cursor, new_list, title):
    old_list = []
    cursor.execute("SELECT episode_link,episode_name from episodes where title=?",
                   (title,))
    data = cursor.fetchall()
    for old_episode in data:
        old_list.append((old_episode[0],old_episode[1].replace("\n", "")))
    list_difference = set(new_list).difference(old_list)
    logging.info(list_difference)
    return list_difference
