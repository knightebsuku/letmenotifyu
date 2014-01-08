
import sqlite3
from notifylib.getmovies import Get_Movies
from notifylib.getseries import Get_Series

class Update:
    def __init__(self,db_file):
        self.connect = sqlite3.connect(db_file)
        self.cursor = self.connect.cursor()
        
    def movie(self):
        movie = Get_Movies(self.cursor,self.connect)
        movie.fetch_new_movies()

    def series(self):
        series = Get_Series(self.cursor,self.connect)
        series_data = series.fetch_series_data()
        for data in series_data:
                all_episodes,new_ep_number,title,current_ep_number,seasons = series.fetch_new_episdoes(data[0],data[1],data[2])
                series.insert_new_epsiodes(all_episodes,new_ep_number,
                                   title,current_ep_number,seasons)

    def get_interval(self):
        self.cursor.execute("SELECT value FROM config WHERE key = 'update_interval'")
        time_int=self.cursor.fetchone()
        return time_int[0]
    
    def start_updates(self):
        try:
            self.series()
            self.movie()
        except Exception as e:
            print(e)
        finally:
            self.connect.close()
    
    













