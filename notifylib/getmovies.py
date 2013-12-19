from urllib.request import Request,urlopen
from bs4 import BeautifulSoup
import re

class Get_Movies:
    def __init__(self,cursor,connect):
        self.cursor=cursor
        self.connect=connect

    def fetch_old_movies(self):
        old_movie_list={}
        self.cursor.execute("SELECT title FROM movies")
        for title in self.cursor.fetchone()
            old_movie_list[title[0]]=''
        return old_movie_list

    def fetch_new_movies(self):
        new_movie_list={}
        request = Request("http://www.primewire.ag/index.php?sort=featured",
                  headers = {'User-Agent':'Mozilla/5.0'})
        featured_movies=urlopen(request).read().decode('UTF-8')
        soup= BeautifulSoup(featured_movies)
        div_class = soup.find_all('div',{'class':'index_item index_item_ie'})
        for links in div_class:
            for movie_links in links.find_all('a',{'href':re.compile("/watch")}):
                title=movie_links['title']
                new_movie_list[title.replace("Watch","")]=movie_links['href']
        return new_movie_list

    def compare(new_list,old_list):
        diff_titles = set(new_listo.keys()) - set(old_list.keys())
        for title in list(diff_titles):
            announce('New Movie',title, http+new_movie_info[title])
            insert_movies.append((title, http+new_movie_info[title]))
        cursor.executemany("INSERT INTO movies(title,link) VALUES(?,?)",insert_movies)
        self.connect.commit()
        
        


                





