
from urllib.request import Request, urlopen
import re

from notifylib.notifiy import announce

def get_movies(cursor, connection):
    """Get latest movies from site"""
    new_movie_info = {}
    req = Request('http://www.primewire.ag/index.php?sort=featured',
                headers = {'User-Agent':'Mozilla/5.0'})
    latest_movie_page= urlopen(req).read().decode('utf-8') #return bytes
    latest_movies = re.findall(r'<div class="index_item index_item_ie"><a href="(.*?)" title="Watch (.*?)">',
                               latest_movie_page)
    for new_info in latest_movies: #get Movies titles and links
        new_movie_info[new_info[1]] = new_info[0]
    compare(new_movie_info, cursor, connection)
        
           
def compare(new_movie_info, cursor, connection):
    old_movie_info = {}
    insert_movies=[]
    http = 'http://primewire.ag'
    cursor.execute("SELECT title FROM movies")
    for top_movie in cursor.fetchall():
        old_movie_info[top_movie[0]] = ""
    diff_titles = set(new_movie_info.keys()) - set(old_movie_info.keys())
    get_difference = list(diff_titles)
    for title in get_difference:
        announce('New Movie',title, http+new_movie_info[title])
        insert_movies.append((title, http+new_movie_info[title]))
    update_database(insert_movies, cursor, connection)
                
def update_database(movie_list, cursor, connection):
        cursor.executemany("INSERT into movies(title,link) VALUES(?,?)", movie_list)
        connection.commit()
