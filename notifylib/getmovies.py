from urllib.request import Request,urlopen
from bs4 import BeautifulSoup
from notifylib.notify import announce
import re

class Get_Movies:
    def __init__(self, cursor, connect):
        self.cursor = cursor
        self.connect = connect

    def fetch_old_movies(self):
        old_movie_list = {}
        self.cursor.execute("SELECT title FROM movies")
        try:
            for title in self.cursor.fetchone():
                old_movie_list[title[0]] = ''
            return old_movie_list
        except Exception:
            old_movie_list["dummy"]="dummy"
            return old_movie_list

    def fetch_new_movies(self):
        request = Request("http://www.primewire.ag/index.php?sort=featured",
                  headers = {'User-Agent':'Mozilla/5.0'})
        featured_movies = urlopen(request).read().decode('UTF-8')
        soup = BeautifulSoup(featured_movies)
        div_class = soup.find_all('div',{'class':'index_item index_item_ie'})
        for links in div_class:
            movies=[]
            for movie_links in links.find_all('a',{'href':re.compile("(/watch|/?genre)")}):
                temp_list=[]
                title = movie_links.get_text()
                movie_title=title.replace("Watch", "")
                links =  movie_links['href']
                temp_list.append([movie_title,links])
            new_data.apend([temp_list[0][0],temp_list[0][1],temp_list[1][0]])
            print(new_data)
            try:
                self.cursor.executemany("INSERT INTO movies(title,link) VALUES(?,?)",new_data)
                self.connect.commit()
                
            except Exception:
                print("Movie Already in the database")

    def compare(self,new_list,old_list):
        diff_titles = set(new_list.keys()) - set(old_list.keys())
        insert_movies=[]
        http="www.primewire.ag"
        for title in list(diff_titles):
            announce('New Movie',title, http+new_list[title])
            insert_movies.append((title, http+new_list[title]))
        self.cursor.executemany("INSERT INTO movies(title,link) VALUES(?,?)",insert_movies)
        self.connect.commit()
        
        


                





