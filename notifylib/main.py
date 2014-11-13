import sqlite3
import re
import logging

from datetime import datetime, timedelta
from gi.repository import Gtk, GObject, Gdk
from notifylib import gui
from notifylib.torrent import Torrent
from notifylib import util
from notifylib.threads import RunUpdate

GObject.threads_init()

class Main(object):
    "Main application"
    def __init__(self, db):
        self.connect = sqlite3.connect(db)
        self.cursor = self.connect.cursor()
        self.db_file = db
        self.builder = Gtk.Builder()
        self.image = Gtk.Image()
        self.torrent = Torrent(self.cursor)
        self.flag = ""
        self.builder.add_from_file("ui/main.glade")
        signals = {'on_AppWindow_destroy': Gtk.main_quit,
                   'on_HeaderView_event': self.on_header_view_event,
                   #'on_HeaderView_cursor_changed': self.header_cursor_changed,
                   'on_HeaderView_row_activated': self.header_view_row,
                   'on_GeneralIconView_activated': self.general_view_activate,
                   'on_GeneralIconView_event': self.general_view_event,
                   'on_AddSeries_activate': self.on_AddSeries_activate,
                   'on_Stop_Update_activate': self.on_Stop_Update_activate,
                   'on_Start_Update_activate': self.on_Start_Update_activate,
                   'on_Delete_Series_activate': self.on_Delete_Series_activate,
                   'on_Properties_activate': self.on_Properties_activate,
                   'on_Current_Season_activate': self.on_Current_Season_activate,
                   'on_preferences_activate': self.on_pref_activate,
                   'on_update_activate': self.on_update_activate,
                   'on_Quit_activate': Gtk.main_quit,
                   'on_About_activate': self.on_About_activate,
                   'on_Kickass_activate': self.on_Kickass_activate,
                   'on_Piratebay_activate': self.on_Piratebay_activate}

        self.builder.connect_signals(signals)
        self.header_dic = {'Movie Archive': self.movie_archive,
                      'Latest Movies': self.latest_movies,
                      'Latest Episodes': self.latest_episodes,
                      'Active Series': self.active_series,
                      'Series Archive': self.series_archive}
        self.general_model = self.builder.get_object("General")
        self.general_icon_view = self.builder.get_object('GeneralIconView')
        self.cell_text = self.builder.get_object("CellRenderText")
        util.pre_populate_menu(self.builder,self.image)
        self.builder.get_object('AppWindow').show()
        #self.update = RunUpdate(self.db_file)
        #self.update.setDaemon(True)
        #self.update.start()
        Gtk.main()

    def general_view_activate(self, widget, choice):
        if self.flag == "latest movies":
            util.open_page(self.cursor, choice, "movie")
        elif self.flag == "latest episodes":
            util.open_page(self.cursor, self.latest_dict[choice])
        elif self.flag == "movie archive":
            self.movie_archive_select(choice)
        elif self.flag == "genre select":
            util.open_page(self.cursor, choice, "movie")
        elif self.flag == "active series":
            self.active_series_select(choice)
        elif self.flag == "select series":
            util.open_page(self.cursor, self.active_series_dic[choice])
        elif self.flag == "series archive":
            self.series_archive_select(choice)
        elif self.flag == "no seasons":
            self.no_season_select(choice)
        elif self.flag == "season select":
            util.open_page(self.cursor, self.archive_series_dict[choice])

    def general_view_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            path = widget.get_path_at_pos(event.x, event.y)
            if path != None:
                widget.select_path(path)
                choice = util.get_selection(widget, self.general_model)
                self.striped_name = choice.split(" Season")[0]
                if event.button == 1:
                    self.general_view_activate(widget, choice)
                elif event.button == 3 and self.flag == "series archive":
                    self.builder.get_object("Series").popup(None, None, None, None,
                                                            event.button, event.time)
                elif event.button == 3 and self.flag == "active series":
                    self.builder.get_object("Series").popup(None, None, None, None,
                                                            event.button, event.time)
                elif event.button == 3 and self.flag == "latest episodes":
                    self.torrent.query(choice)
                    self.builder.get_object("torrents").popup(None, None, None, None,
                                                       event.button, event.time)

    def on_header_view_event(self, widget, event):
        if event.button == 1:
            selection = widget.get_selection()
            name, itr = selection.get_selected()
            header_choice = name[itr][1]
            try:
                self.header_dic[header_choice]()
            except KeyError:
                pass

    def header_view_row(self, widget, event, selection):
        print("row activated")
        #selection.s
        #color = Gdk.RGBA(blue=0.5)
        #color.parse('#003399')
        #self.cell_text.set_property("cell-background-rgba",color)

    def movie_archive_select(self,choice):
        self.cursor.execute("SELECT id from genre where genre=?",
                                (choice,))
        genre_key = self.cursor.fetchone()
        self.cursor.execute("SELECT title,path from movies " +
                                "join movie_images on  movies.id=movie_images.movie_id "+
                                "and  movies.genre_id=?",
                                (genre_key[0],))
        movie_info = self.cursor.fetchall()
        self.general_model.clear()
        for results in movie_info:
            util.render_view(self.image, results[0],
                                 self.general_model, results[1])
        self.flag = "genre select"

    def active_series_select(self, choice):
        self.active_series_dic = {}
        series_name = choice.split(" Season")[0]
        logging.debug(series_name)
        series_number = choice.split("Season ")[1]
        logging.debug(series_number)
        self.cursor.execute("SELECT episode_name,episode_link " +
                            "FROM episodes WHERE" +
                            ' series_id=(SELECT id from series where title=?)' +
                            ' and episode_link LIKE ?',
                            (series_name, "%season-"+series_number+"%",))
        self.general_model.clear()
        for current_season in self.cursor.fetchall():
            util.render_view(self.image, current_season[0], self.general_model)
            self.active_series_dic[current_season[0]] = current_season[1]
        self.flag = "select series"
        

    def movie_archive(self):
        self.general_model.clear()
        self.cursor.execute("SELECT genre from genre")
        result = self.cursor.fetchall()
        self.image.set_from_file("ui/movies.png")
        pixbuf = self.image.get_pixbuf()
        for genre in result:
            self.general_model.append([pixbuf, genre[0]])
        self.flag = 'movie archive'

    def latest_movies(self):
        self.general_model.clear()
        self.cursor.execute("SELECT value from config where key='movie_duration'")
        duration = self.cursor.fetchone()
        week = datetime.now() - timedelta(days=int(duration[0]))
        self.cursor.execute("SELECT title,path from movies "+
                            "join movie_images "+
                            "on movies.id=movie_id and "+
                            "movies.date_added BETWEEN ? and ? order by title",
                            (week, datetime.now(),))
        movies = self.cursor.fetchall()
        for movie in movies:
            util.render_view(self.image, movie[0], self.general_model, movie[1])
        self.flag = 'latest movies'

    def latest_episodes(self):
        self.latest_dict = {}
        self.general_model.clear()
        self.cursor.execute("SELECT value from config where key='series_duration'")
        duration = self.cursor.fetchone()
        week = datetime.now() - timedelta(days=int(duration[0]))
        self.cursor.execute("SELECT episode_name,episode_link,path from episodes "+
                            "join series_images "+
                            "on episodes.series_id=series_images.series_id "+
                            "and episodes.Date BETWEEN ? AND ?",
                            (week, datetime.now(),))
        for episode in self.cursor.fetchall():
            util.render_view(self.image, episode[0], self.general_model, episode[2])
            self.latest_dict[episode[0]] = episode[1]
        self.flag = 'latest episodes'

    def active_series(self):
        self.general_model.clear()
        self.cursor.execute("SELECT title,current_season,path  from series "+
                            "join series_images on series.id=series_images.series_id and "+
                            "series.status=1 order by title")
        for series in self.cursor.fetchall():
            util.render_view(self.image, series[0]+" "+"Season"+" "+str(series[1]),
                              self.general_model, series[2])
        self.flag = 'active series'

    def series_archive(self):
        self.general_model.clear()
        self.cursor.execute("SELECT title,path  from series join "+
                            "series_images on series.id=series_images.series_id order by title")
        for all_series in self.cursor.fetchall():
            util.render_view(self.image, all_series[0], self.general_model,
                                 all_series[1])
            self.flag = 'series archive'

    def series_archive_select(self,choice):
        self.series_name = choice
        self.cursor.execute("SELECT number_of_seasons from series where title=?",
                            (choice,))
        no_seasons = self.cursor.fetchone()
        index = 1
        self.general_model.clear()
        while index <= int(no_seasons[0]):
            util.render_view(self.image, "Season %s" % index, self.general_model)
            index += 1
        self.flag = "no seasons"
            
    def no_season_select(self,choice):
        self.archive_series_dict = {}
        no = choice.split("Season ")[1]
        self.cursor.execute("SELECT episode_name,episode_link FROM episodes" +
                            ' WHERE series_id=(SELECT id from series where title=?)' +
                            ' and episode_link LIKE ?',
                            (self.series_name, "%season-" + no + "%",))
        self.general_model.clear()
        for current_season in self.cursor.fetchall():
            util.render_view(self.image, current_season[0], self.general_model)
            self.archive_series_dict[current_season[0]] = current_season[1]
        self.flag = "season select"
        

    def on_AddSeries_activate(self,widget):
        gui.Add_Series(self.cursor, self.connect)

    def on_About_activate(self, widget):
        gui.About()

    def on_Piratebay_activate(self, widget):
        self.torrent.piratebay()

    def on_Kickass_activate(self, widget):
        self.torrent.kickass()

    def on_Stop_Update_activate(self, widget):
        gui.Confirm(self.striped_name, "stop", self.connect, self.cursor)

    def on_Start_Update_activate(self, widget):
        gui.Confirm(self.striped_name, "start", self.connect, self.cursor)

    def on_Delete_Series_activate(self, widget):
        gui.Confirm(self.striped_name, "delete", self.connect, self.cursor)

    def on_Properties_activate(self, widget):
        gui.Statistics(self.striped_name, self.connect, self.cursor)

    def on_pref_activate(self, widget):
        gui.Preferences(self.cursor, self.connect)

    def on_Current_Season_activate(self, widget):
        gui.Current_Season(self.cursor, self.connect, self.striped_name)

    def on_update_activate(self, widget):
        "Stop current updating thread and start new one"
        self.update.stop()
        logging.info("Stopping current thead")
        new_thread = RunUpdate(self.db_file)
        new_thread.setDaemon(True)
        new_thread.start()
        logging.info("Starting new thread")
