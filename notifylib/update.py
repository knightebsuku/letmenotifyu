
import sqlite3
import time
from notifylib.getmovies import Get_Movies
from notifylib.getseries import Get_Series

class Update:
    def __init__(self,db_file):
        self.connect = sqlite3.connect(db_file)
        self.cursor = self.connect.cursor()
        
    def movie(self):
        movie = Get_Movies(self.cursor,self.connect)
        old = movie.fetch_old_movies()
        new = movie.fetch_new_movies()
        movie.compare(new,old)

    def series(self):
        series = Get_Series(self.cursor,self.connect)
        series_data = series.fetch_series_data()
        for data in series_data:
                all_episodes,new_ep_number,title,current_ep_number,seasons = series.fetch_new_episdoes(data[0],data[1],data[2])
                series.insert_new_epsiodes(all_episodes,new_ep_number,
                                   title,current_ep_number,seasons)

    def interval(self):
        self.cursor.execute("SELECT value FROM config WHERE key = 'update_interval'")
        time=self.cursor.fetchone()
        return time[0]
        

def start_updates(db_file):
    check_updates=Update(db_file)
    while True:
        try:
            #check_updates.series()
            check_updates.movie()
            sleep=check_updates.interval()
            time.sleep(int(sleep))
        except Exception as e:
            print(e)
            print("cant update")
            time.sleep(300)
    
    













