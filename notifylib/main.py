#!/usr/bin/python3

import sqlite3 as sqlite
import webbrowser
import re

from datetime import datetime, timedelta
from gi.repository import Gtk,GObject
from threading import Thread
from notifylib.add_url import Add_Series
from notifylib.about import About
from notifylib.confirm import Confirm
from notifylib.create_tree_view import create_parent
from notifylib.update import update_movie_series

GObject.threads_init()


class Main:
    """Main Page for letmenotifyu"""
    def __init__(self, gladefile, pic, db):
        self.connect = sqlite.connect(db)
        self.cur = self.connect.cursor()
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        signals = {'on_winlet_destroy': self.on_winlet_destroy,
                 'on_imageAdd_activate': self.on_imageAdd_activate,
                 'on_imageQuit_destroy': self.on_imageQuit_destroy,
                 'on_imageAbout_activate': self.on_imageAbout_activate,
                 'on_notebook1_button_press_event': self.on_notebook1_button_press_event,
                 'on_treeviewMovies_button_press_event': self.on_treeviewMovies_button_press_event,
                 'on_treeview1_button_press_event': self.on_treeview1_button_press_event}
        
        self.builder.connect_signals(signals)
        self.treeviewMovies=self.builder.get_object('treeviewMovies')
        self.treeview1=self.builder.get_object('treeview1')
        self.series_archive=self.builder.get_object('treeSeriesArchive')
        self.treeLatest=self.builder.get_object('treeLatest')
        self.notebook1 = self.builder.get_object('notebook1')
        self.window = self.builder.get_object('winlet')
        self.window.show()
        Gtk.main()

    def on_winlet_destroy(self,widget):
        self.connect.close()
        Gtk.main_quit()

    def on_imageAdd_activate(self,widget):
        Add_Series('input7.glade',self.cur,self.connect)

    def on_imageQuit_destroy(self,widget):
        self.connect.close()
        Gtk.main_quit()

    def on_imageAbout_activate(self,widget):
        About('about7.glade')

    def on_treeviewMovies_button_press_event(self,widget,event):
        if event.button == 1:
            get_title=self.builder.get_object('treeviewMovies').get_selection()
            movie,name=get_title.get_selected()
            fetch_title=movie[name][0]
            self.cur.execute("SELECT link from movies where title=?",(fetch_title,))
            for link in self.cur.fetchall():
                webbrowser.open_new(link[0])
                
    def on_treeview1_button_press_event(self,widget,event):
        if event.button == 1:
            selected=self.builder.get_object('treeview1').get_selection()
            series,name=selected.get_selected()
            episode=series[name][0]
            if re.match(r"^Episode",episode):
                path=self.series_archive.get_path(name)
                path_value = str(path)

                episode_title_path=self.series_archive.get_iter(path_value[:1])
                episode_season_path=self.series_archive.get_iter(path_value[:3])
                episode_path=self.series_archive.get_iter(path_value)

                model = self.treeview1.get_model()
                episode_title = model.get_value(episode_title_path, 0) 
                episode_season = model.get_value(episode_season_path, 0)
                episode_path = model.get_value(episode_path, 0)
                sql_season = episode_season.replace(" ", "-")

                self.cur.execute("SELECT episode_link from episodes where episode_name=? and title=? and episode_link LIKE ?",
                                    (episode_path, episode_title, "%"+sql_season+"%"))
                for link in self.cur.fetchall():
                    webbrowser.open_new("http://www.primewire.ag"+link[0])
                
            
    def on_notebook1_button_press_event(self,widget,event):
            if self.notebook1.get_current_page()==0:
                    self.builder.get_object('listMovies').clear()
                    self.cur.execute('SELECT title FROM movies')
                    for title in self.cur.fetchall():
                            self.builder.get_object('listMovies').append([title[0]])
            elif self.notebook1.get_current_page() == 1:
                    self.series_archive.clear()
                    create_parent(self.cur,self.builder.get_object('treeSeriesArchive'))
            elif self.notebook1.get_current_page == 2:
                    week = datetime.now() - timedelta(days=7)
                    self.builder.get_object('listLatestSeries').clear()
                    self.cur.execute('SELECT title,episode_link,episode_name from episodes WHERE Date BETWEEN  ? AND ?',(datetime.now(),week))
                    for latest in self.cur.fetchall():
                            self.builder.get_object('listLatestSeries').append([latest[0]])
            else:
                    pass
                
                    
            
            
