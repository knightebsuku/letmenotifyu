from urllib.request import Request,urlopen
from bs4 import BeautifulSoup
from notifylib.notify import announce
import re

class Get_Movies:
    def __init__(self, cursor, connect):
        self.cursor = cursor
        self.connect = connect

    def fetch_new_movies(self):
        request = Request("http://www.primewire.ag/index.php?sort=featured",
                  headers = {'User-Agent':'Mozilla/5.0'})
        featured_movies = urlopen(request).read().decode('UTF-8')
        soup = BeautifulSoup(featured_movies)
        div_class = soup.find_all('div',{'class':'index_item index_item_ie'})
        for links in div_class:
            new_data = []
            temp_list = []
            for movie_links in links.find_all('a',{'href':re.compile("(/watch|/?genre)")}):
                title = movie_links.get_text()
                movie_title=title.replace("Watch", "")
                links =  movie_links['href']
                temp_list.append([movie_title,links])
            new_data.append([temp_list[0][0],temp_list[0][1],temp_list[1][0]])
            try:
                self.cursor.execute("INSERT INTO genre(genre) VALUES(?)",(temp_list[1][0],))
                self.connect.commit()
            except Exception as e:
                print("")
            try:
                self.cursor.execute("SELECT Id from genre where genre=?",(temp_list[1][0],))
                key = self.cursor.fetchone()
                self.cursor.execute("INSERT INTO movies(title,link,genre_id) VALUES(?,?,?)",
                                        (temp_list[0][0],temp_list[0][1],int(key[0]),))
                self.connect.commit()
                announce('New Movie',temp_list[0][0],temp_list[0][1])
            except Exception as e:
                print("")
        


                





