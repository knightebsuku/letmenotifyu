from urllib.request import Request,urlopen
from bs4 import BeautifulSoup
from datetime import datetime
from notifylib.notify import announce
import re

class Get_Series:
    def __init__(self,cursor,connect):
        self.cursor = cursor
        self.connect =  connect

    def get_page(self,episode_site):
        req=Request(episode_site, headers={'User-Agent':'Mozilla/5.0'})
        data=urlopen(req).read().decode('ISO-8859-1')
        soup=BeautifulSoup(data)
        return soup
        
    def fetch_series_data(self):
        self.cursor.execute('SELECT title,series_link,number_of_episodes from series where status=1')
        return self.cursor.fetchall()

    def fetch_new_episdoes(self, title,link,eps):
        episode_page_data=self.get_page(link)
        all_series_info = []
        div_class = episode_page_data.find_all('div',{'class':'tv_episode_item'})
        for links in div_class:
            for series_links in  links.find_all('a'):
                all_series_info.append([series_links.get('href'),links.get_text().replace(" ","")])
        seasons = episode_page_data.find("h2")
        return all_series_info,len(all_series_info),title,eps,len(seasons)

    def insert_new_epsiodes(self,all_eps,ep_number,title,old_ep_number,no_seasons):
        diff = ep_number - old_ep_number
        while diff > 0:
            self.cursor.execute("INSERT INTO episodes(title,episode_link,episode_name,Date) VALUES(?,?,?,?)",(title,all_eps[-diff][0],all_eps[-diff][1],datetime.now(),))
            self.connect.commit()
            announce("New Series Episode",title,"www.primewire.ag"+all_eps[-diff][0])
            diff-=1
        self.cursor.execute("UPDATE series set number_of_episodes=?,number_of_seasons=?,last_update=?  where title=?",
                            (ep_number,no_seasons,datetime.now(),title,))
        self.connect.commit()
            
            
        
        
                    
            




