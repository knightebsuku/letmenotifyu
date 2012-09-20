#!/usr/bin/python

# import staandard python libs and custom ones.
import os,webbrowser,sys
from gi.repository import Gtk, GObject
from pysqlite2 import dbapi2 as sqlite
from notifylib.add_url import Series
from notifylib.about import About
from notifylib.confirm import Confirm


GObject.threads_init()
movie_path=os.environ['HOME']+'/.local/share/letmenotifyu/movies.db'
series_path=os.environ['HOME']+'/.local/share/letmenotifyu/url.db'
path=os.path.join('/usr/share/letmenotifyu','ui')
os.chdir(path)

         
class Base:
    """Font end for letmenotifyu"""
    def __init__(self,gladefile,movie_db,series_db,pic):
        self.movies_db=movie_db
        self.series_db=series_db
        #set the glade file
        self.builder=Gtk.Builder()
        self.builder.add_from_file(gladefile)
        dict={'on_btnmovies_clicked':self.on_btnmovies_clicked,
              'on_winlet_destroy':self.on_winlet_destroy,
              'on_treeview1_button_press_event':self.on_treeview1_button_press_event,
              'on_btnSeries_clicked':self.on_btnSeries_clicked,
              'on_additem_button_press_event':self.on_additem_button_press_event,
              'on_closeitem_button_press_event':self.on_closeitem_button_press_event,
              'on_aboutitem_button_press_event':self.on_aboutitem_button_press_event}
        self.builder.connect_signals(dict) #waiting for Signals
        self.window=self.builder.get_object('winlet') #name of main gtkwindow object
        self.window.set_icon_from_file(pic)

        self.window.show() #Show file
        
    def on_winlet_destroy(self,widget):
        Gtk.main_quit() #close GtkWindow

    def on_btnSeries_clicked(self,widget):
        self.builder.get_object('listmovies').clear() #in case there is stuff
        series=self.builder.get_object('listmovies')
        connect=sqlite.connect(self.series_db) #url.db
        db=connect.cursor()
        db.execute("SELECT * from series")
        for links in db.fetchall():
            series.append([links[3]])
        
    def on_btnmovies_clicked(self,widget):
        self.builder.get_object('listmovies').clear() #in case there is stuff
        store=self.builder.get_object('listmovies')
        connect=sqlite.connect(self.movies_db)
        db=connect.cursor()
        db.execute("SELECT * FROM movie")
        for title in db.fetchall():
            store.append([title[1]])

    def on_treeview1_button_press_event(self,widget,event):
        if event.button==1:
            choosen=self.builder.get_object('treeview1').get_selection() #reference to GTK.Selection
            movie,name=choosen.get_selected() #returns tuple
            title=movie[name][0]
            if title[-5:-1]=="2012":
                connect=sqlite.connect(self.movies_db)
                db=connect.cursor()
                db.execute("SELECT link FROM movie WHERE titles=?",(title,))
            else:
                connect=sqlite.connect(self.series_db)
                db=connect.cursor()
                db.execute("SELECT eplat FROM series WHERE title=?", (title,))
            for link in db.fetchall():
                webbrowser.open_new(link[0])
                
        elif event.button==3:
            choosen=self.builder.get_object('treeview1').get_selection() #reference to GTK.Selection
            series,name=choosen.get_selected() #returns tuple
            url=series[name][0]
            if url[-5:-1]!="2012":
                load=Confirm('confirm.glade',url,self.series_db)
                
        else:
            ""

    def on_additem_button_press_event(self,widget,event):
        load=Series('inputDialog.glade',self.series_db)
        
    def on_closeitem_button_press_event(self,widget,event):
        Gtk.main_quit()
        
    def on_aboutitem_button_press_event(self,widget,event):
        load=About('about.glade')




