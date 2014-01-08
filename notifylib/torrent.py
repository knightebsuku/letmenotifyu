
import webbrowser

class Torrent:
        def __init__(self,title,cursor,connect):
                self.title=title
                self.cursor=cursor
                self.connect=connect
                self.split_title=self.title.split("-")
                
        def kickass(self):
                self.cursor.execute("Select name from torrents where id=1")
                result=self.cursor.fetchone()
                webbrowser.open_new(result[0]+self.split_title[0])
                
        def isohunt(self):
                self.cursor.execute("SELECT name from torrents where id=3")
                result=self.cursor.fetchone()
                webbrowser.open_new(result[0]+self.split_title[0])
                
        def piratebay(self):
                self.cursor.execute("SELECT name FROM torrents where id=2")
                result=self.cursor.fetchone()
                webbrowser.open_new(result[0]+self.split_title[0])
                
        def online(self,dic):
                webbrowser.open_new(dic[self.title])
