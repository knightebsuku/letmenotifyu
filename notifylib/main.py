
import sqlite3
import webbrowser
import re

from datetime import datetime, timedelta
from gi.repository import Gtk,GObject
from threading import Thread
from notifylib.add_url import Add_Series
from notifylib.about import About
from notifylib.confirm import Confirm,Torrent,check_updates
from notifylib.update import get_updates
from notifylib.stats import Statistics

GObject.threads_init()

class Main:
    def __init__(self, gladefile, pic, db):
        self.connect= sqlite3.connect(db)
        self.cursor= self.connect.cursor()
        self.db_file=db
        self.latest_dict = {}
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        signals = {'on_winlet_destroy': self.on_winlet_destroy,
                 'on_imageAdd_activate': self.on_imageAdd_activate,
                 'on_imageQuit_destroy': self.on_imageQuit_destroy,
                 'on_imageAbout_activate': self.on_imageAbout_activate,
                 'on_notebook1_button_press_event': self.on_notebook1_button_press_event,
                 'on_treeviewMovies_button_press_event': self.on_treeviewMovies_button_press_event,
                 'on_treeArchive_button_press_event': self.on_treeArchive_button_press_event,
                 'on_treeLatest_button_press_event':self.on_treeLatest_button_press_event,
                 'on_Stop_Update_activate':self.on_Stop_Update_activate,
                 'on_Start_Update_activate':self.on_Start_Update_activate,
                 'on_Delete_Series_activate':self.on_Delete_Series_activate,
                 'on_Properties_activate':self.on_Properties_activate,
                 'on_Isohunt_activate':self.on_Isohunt_activate,
                 'on_Kickass_activate':self.on_Kickass_activate,
                 'on_Piratebay_activate':self.on_Piratebay_activate,
                 'on_online_video_activate':self.on_online_video_activate,
                 'on_Update_activate':self.on_Update_activate}
        
        self.builder.connect_signals(signals)
        self.treeArchive = self.builder.get_object('treeArchive')
        self.series_archive = self.builder.get_object('treeSeriesArchive')
        self.notebook1 = self.builder.get_object('notebook1')
        self.window = self.builder.get_object('winlet').show()
        #self.update_thread = Thread(target=get_updates,args=(self.db_file,))
        #self.update_thread.setDaemon(True)
        #self.update_thread.start()
        Gtk.main()

    def on_winlet_destroy(self,widget):
        Gtk.main_quit()

    def on_imageAdd_activate(self,widget):
        Add_Series('input7.glade',self.cursor,self.connect)

    def on_imageQuit_destroy(self,widget):
        Gtk.main_quit()

    def on_imageAbout_activate(self,widget):
        About('about7.glade')

    def on_Update_activate(self,widget):
        check_updates(self.update_thread,self.db_file)

    def on_treeviewMovies_button_press_event(self,widget,event):
        if event.button == 1:
            get_title= self.builder.get_object("treeviewMovies").get_selection()
            movie,name= get_title.get_selected()
            fetch_title= movie[name][0]
            self.cursor.execute("SELECT link FROM movies WHERE title=?",(fetch_title,))
            link=self.cursor.fetchone()
            webbrowser.open_new(link[0])

    def on_treeLatest_button_press_event(self,widget,event):
        if event.button==3:
            get_latest_series=self.builder.get_object("treeLatest").get_selection()
            latest,name=get_latest_series.get_selected()
            self.get_episode=latest[name][0]
            self.torrent=Torrent(self.get_episode,self.cursor,self.connect)
            self.builder.get_object("torrents").popup(None,None,None,None,
                                                       event.button,event.time)

    def on_Isohunt_activate(self,widget):
        self.torrent.isohunt()

    def on_Piratebay_activate(self,widget):
        self.torrent.piratebay()
    
    def on_Kickass_activate(self,widget):
        self.torrent.kickass()
        
    def on_online_video_activate(self,widget):
        self.torrent.online(self.latest_dict)
    
        
    def on_treeArchive_button_press_event(self,widget,event):
        if event.button == 1:
            selected = self.treeArchive.get_selection()
            series,name = selected.get_selected()
            episode = series[name][0]
            if re.match(r"^Episode",episode):
                path = self.series_archive.get_path(name)
                path_value = str(path).split(":")

                episode_title_path = self.series_archive.get_iter(path_value[0])
                episode_season_path = self.series_archive.get_iter(path_value[0]+":"+path_value[1])
                episode_path = self.series_archive.get_iter(path_value[0]+":"+
                                                            path_value[1]+":"+path_value[2])
                
                model = self.treeArchive.get_model()
                episode_title = model.get_value(episode_title_path, 0) 
                episode_season = model.get_value(episode_season_path, 0)
                episode = model.get_value(episode_path, 0)
                sql_season = episode_season.replace(" ", "-")
                
                self.cursor.execute("SELECT episode_link FROM episodes WHERE episode_name=? AND title=? AND episode_link LIKE ?",
                                    (episode, episode_title, "%"+sql_season+"%"))
                link=self.cursor.fetchone()
                webbrowser.open_new("http://www.primewire.ag"+link[0])
            else:
                pass
        elif event.button == 3:
            selected = self.treeArchive.get_selection()
            series,name = selected.get_selected()
            self.series_title = series[name][0]
            title=self.series_archive.get_path(name)
            try:
                int(str(title))
                self.builder.get_object("Series").popup(None,None,None,None,
                                                        event.button,event.time)
            except ValueError as e:
                pass
            
    def on_Stop_Update_activate(self,widget):
        Confirm('confirm7.glade',self.series_title,"stop",self.connect,self.cursor)
        
    def on_Start_Update_activate(self,widget):
        Confirm('confirm7.glade',self.series_title,"start",self.connect,self.cursor)
        
    def on_Delete_Series_activate(self,widget):
        Confirm('confirm7.glade',self.series_title,"delete",self.connect,self.cursor)

    def on_Properties_activate(self,widget):
        Statistics('stats7.glade',self.series_title,self.connect,self.cursor)
                  
    def on_notebook1_button_press_event(self,widget,event):
        if self.notebook1.get_current_page() == 0:
            self.builder.get_object('listMovies').clear()
            self.cursor.execute('SELECT title FROM movies ORDER BY id DESC')
            for title in self.cursor.fetchall():
                self.builder.get_object('listMovies').append([title[0]])
        elif self.notebook1.get_current_page() == 1:
            self.series_archive.clear()
            create_parent(self.cursor,self.builder.get_object('treeSeriesArchive'))
        elif self.notebook1.get_current_page() == 2:
            week = datetime.now() - timedelta(days=7)
            self.builder.get_object('listLatestSeries').clear()
            self.cursor.execute('SELECT title,episode_link,episode_name FROM episodes WHERE Date BETWEEN  ? AND ?',
                                (week, datetime.now()))
            for latest in self.cursor.fetchall():
                self.latest_dict[latest[0]+"-"+latest[2]] = "http://www.primewire.ag"+latest[1]
                self.builder.get_object('listLatestSeries').append([latest[0]+"-"+latest[2]])

        else:
            pass

def create_parent(cursor, series_column):
    x=1
    cursor.execute("SELECT title,number_of_seasons from series where status=1")
    for results in cursor.fetchall():
        parent_title = series_column.append(None, [results[0]])
        while x <= int(results[1]):
            create_episodes(cursor, results[0], parent_title, series_column, x)
            x += 1
        x = 1

def create_episodes(cursor, series_title, parent_title, series_column, x):
    name = "season "+str(x)
    sql_name = "%season-"+str(x)+"%"
    series_number = series_column.append(parent_title, [name])
    cursor.execute("SELECT episode_name FROM episodes WHERE title=? and episode_link LIKE ?", (series_title, sql_name))
    for episode in cursor.fetchall():
        series_column.append(series_number, [episode[0]])
    
            
            






