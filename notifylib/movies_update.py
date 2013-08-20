
from urllib.request import Request, urlopen
import re

from notifylib.notifiy import announce

def get_movies(cursor, connection):
    """Get latest movies from site"""
    movie_info = []
    req = Request('http://www.primewire.ag/index.php?sort=featured',
                headers = {'User-Agent':'Mozilla/5.0'})
    latest_movie_page= urlopen(req).read()
    latest_movies = re.findall(b'<div class="index_item index_item_ie"><a href=(.*?) title="Watch (.*?)">',
                               latest_movie_page)
    for new_info in latest_movies: #get Movies titles and links
        movie_info.append((new_info[1], new_info[0]))
    #compare(movie_info, cursor, connection)
        
           
def compare(movie_info, cursor, connection):
    cursor.execute("SELECT title FROM movies WHERE id=1")
    for top_movie in cursor.fetchall():
        if top_movie != movie_info[0][0]:
            print("Going to annnounce")
            print(movie_info[0][0])
            #announce('New Movie', movie_info[0][0],movie_info[0][1])
    #update_database(movie_info,cursor, connection)
                
def update_database(movie_info, cursor, connection):
    for movie_detail in movie_info:
        cursor.excute("INSERT into movies(title,link) VALUES(?,?)",
                      (movie_detail[0],movie_detail[1],))
        connection.commit()
