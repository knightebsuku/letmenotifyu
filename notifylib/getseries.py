from datetime import datetime
from notifylib.notify import announce
from notifylib.website import primewire,watchseries
import re
import logging

class Get_Series:
    def __init__(self, cursor, connect):
        self.cursor = cursor
        self.connect =  connect

    def fetch_series_data(self):
        self.cursor.execute('SELECT title,series_link,number_of_episodes from series where status=1')
        return self.cursor.fetchall()

    def fetch_new_episdoes(self, title, link, eps):
        if re.match(r'http://www.primewire.ag',link):
            return primewire(title,link,eps)
        elif re.match(r'http://www.watchseries.to/',link):
            return watchseries(title,link,eps)
        else:
            logging.info(link)
            logging.error("Link is not registed with any website")
            
    def insert_new_epsiodes(self, all_eps, ep_number, title, old_ep_number, no_seasons):
        diff = ep_number - old_ep_number
        if old_ep_number == 0:
            while diff > 0:
                self.cursor.execute("INSERT INTO episodes(title,episode_link,episode_name) VALUES(?,?,?)",(title, all_eps[-diff][0], all_eps[-diff][1],))
                self.connect.commit()
                diff-=1
            self.cursor.execute("UPDATE series set number_of_episodes=?,number_of_seasons=?,last_update=?  where title=?",
                            (ep_number, no_seasons, datetime.now(),title,))
            self.connect.commit()
            logging.info(" Series Added: "+ title)
            announce("New Series Added",title)
        else:
            while diff > 0:
                self.cursor.execute("INSERT INTO episodes(title,episode_link,episode_name,Date) VALUES(?,?,?,?)",(str(title).title, all_eps[-diff][0], all_eps[-diff][1], datetime.now(),))
                self.connect.commit()
                announce("New Series Episode",title,"www.primewire.ag"+all_eps[-diff][0])
                diff-=1
            self.cursor.execute("UPDATE series set number_of_episodes=?,number_of_seasons=?,last_update=?  where title=?",
                            (ep_number, no_seasons, datetime.now(),title,))
            self.connect.commit()

 
        
        
                    
            




