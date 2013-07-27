#!/usr/bin/python

import os
import webbrowser
import re
import sqlite3 as sqlite

from gi.repository import Gtk, GObject
from threading import Thread
from notifylib.add_url import Add_Series
from notifylib.about import About
from notifylib.confirm import Confirm
from notifylib.create_tree_view import create_parent
from notifylib.update import update_databases

sqlite_file = os.environ['HOME']+'/.local/share/letmenotifyu/letmenotifyu.sqlite'
GObject.threads_init()


class Base:
    """Font end for letmenotifyu"""
    def __init__(self, gladefile, pic, sqlite_file):
        self.connection = sqlite.connect(sqlite_file)
        self.cursor = self.connection.cursor()
        self.builder = Gtk.Builder()        
        self.builder.add_from_file(gladefile)
        dict = {'on_btnmovies_clicked': self.on_btnmovies_clicked,
              'on_winlet_destroy': self.on_winlet_destroy,
              'on_treeview1_button_press_event': self.on_treeview1_button_press_event,
              'on_btnSeries_clicked': self.on_btnSeries_clicked,
              'on_additem_button_press_event': self.on_additem_button_press_event,
              'on_closeitem_button_press_event': self.on_closeitem_button_press_event,
              'on_aboutitem_button_press_event': self.on_aboutitem_button_press_event}
        self.builder.connect_signals(dict)
        self.TreeSeries = self.builder.get_object('TreeSeries')
        self.treeview = self.builder.get_object('treeview1')
        self.listmovies = self.builder.get_object('listmovies')
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.connection.commit()
        self.window = self.builder.get_object('winlet')
        self.window.set_icon_from_file(pic)
        self.window.show()
        update_thread = Thread(target= update_databases)
        update_thread.setDaemon(True)
        update_thread.start()
        Gtk.main()
        
    def on_winlet_destroy(self, widget):
        Gtk.main_quit()

    def on_btnSeries_clicked(self, widget):
        self.treeview.set_model(self.TreeSeries)
        self.TreeSeries.clear()
        create_parent(self.cursor, self.TreeSeries)
                
    def on_btnmovies_clicked(self, widget):
        self.listmovies.clear()
        self.treeview.set_model(self.listmovies)
        self.cursor.execute("SELECT title FROM movies")
        for title in self.cursor.fetchall():
            self.listmovies.append([title[0]])

    def on_treeview1_button_press_event(self, widget, event):
        if event.button == 1:
            choosen=self.treeview.get_selection()
            movie, name = choosen.get_selected()
            title = movie[name][0]
            if re.findall(r"\(\d{4}\)$", title):
                self.cursor.execute("SELECT link FROM movies WHERE title=?", (title,))
            elif re.findall(r"^Episode", title):
                path = self.TreeSeries.get_path(name)
                path_value = str(path)
                
                episode_title_path = self.TreeSeries.get_iter(path_value[:1])
                episode_season_path = self.TreeSeries.get_iter(path_value[:3])
                episode_path = self.TreeSeries.get_iter(path_value)

                model = self.treeview.get_model()
                episode_title = model.get_value(episode_title_path, 0) 
                episode_season = model.get_value(episode_season_path, 0)
                episode_path = model.get_value(episode_path, 0)
                sql_season = episode_season.replace(" ", "-")
                
                self.cursor.execute("SELECT episode_link from episodes where episode_name=? and title=? and episode_link LIKE ?", (episode_path, episode_title, "%"+sql_season+"%"))
            for link in self.cursor.fetchall():
                webbrowser.open_new(link[0])
                
        elif event.button == 3:
            choosen = self.builder.get_object('treeview1').get_selection()
            series, name = choosen.get_selected()
            url = series[name][0]
            if re.findall(r"\d{4}$", url):
                pass
            else:
                Confirm('confirm.glade', url, self.cursor, self.connection)

    def on_additem_button_press_event(self, widget, event):
        Add_Series('inputDialog.glade', self.cursor, self.connection)
        
    def on_closeitem_button_press_event(self, widget, event):
        self.connection.close()
        Gtk.main_quit()
        
    def on_aboutitem_button_press_event(self, widget, event):
        About('about.glade')




