import sqlite3
import re
import logging

from datetime import datetime, timedelta
from gi.repository import Gtk, GObject, Gdk
from notifylib import gui
from notifylib.torrent import Torrent
from notifylib import util
from notifylib.threads import RunUpdate, FetchPosters

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
        self.builder.add_from_file("ui/main.glade")
        self.active_series_view = self.builder.get_object("ActiveSeries")
        self.active_series_view.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        signals = {'on_AppWindow_destroy': Gtk.main_quit,
                   'on_headers_event': self.on_headers_event,
                   'on_GenreIcon_activated': self.on_GenreIcon_activated,
                   'on_LatestMovie_activated': self.on_LatestMovie_activated,
                   'on_LatestEpisodesIcon_activated': self.on_LatestEpisodes_activated,
                   'on_LatestEpisodesIcon_event': self.on_LatestEpisodes_event,
                   'on_SeriesArchive_activated': self.on_SeriesArchive_activated,
                   'on_ActiveSeries_activated': self.on_ActiveSeries_activated,
                   'on_ActiveSeries_button_event': self.on_ActiveSeries_event,
                   'on_AddSeries_activate': self.on_AddSeries_activate,
                   'on_Stop_Update_activate': self.on_Stop_Update_activate,
                   'on_Start_Update_activate': self.on_Start_Update_activate,
                   'on_Delete_Series_activate': self.on_Delete_Series_activate,
                   'on_Properties_activate': self.on_Properties_activate,
                   'on_Current_Season_activate': self.on_Current_Season_activate,
                   'on_preferences_activate': self.on_pref_activate,
                   'on_update_activate': self.on_update_activate,
                   'on_poster_update_activate': self.on_poster_update_activate,
                   'on_Quit_activate': Gtk.main_quit,
                   'on_About_activate': self.on_About_activate,
                   'on_Kickass_activate': self.on_Kickass_activate,
                   'on_Piratebay_activate': self.on_Piratebay_activate}

        self.builder.connect_signals(signals)
        self.general_model = self.builder.get_object("General")
        self.genre_icon_view = self.builder.get_object("GenreIcon")
        self.latest_episodes_view = self.builder.get_object("LatestEpisodesIcon")
        self.builder.get_object('AppWindow').show()
        self.update = RunUpdate(self.db_file)
        self.update.setDaemon(True)
        self.update.start()
        Gtk.main()

    def on_headers_event(self, widget, event):
        headers = self.builder.get_object("headers")
        if headers.get_current_page() == 0:
            self.general_model.clear()
            self.cursor.execute("SELECT value from config where key='movie_duration'")
            duration = self.cursor.fetchone()
            week = datetime.now() - timedelta(days=int(duration[0]))
            self.cursor.execute("SELECT title,path from movies join movie_images on movies.id=movie_id and movies.date_added BETWEEN ? and ? order by title",
                                (week, datetime.now(),))
            movies = self.cursor.fetchall()
            for movie in movies:
                util.render_view(self.image,movie[0], self.general_model,movie[1])
        elif headers.get_current_page() == 1:
            self.general_model.clear()
            self.genre_icon_view.set_model(self.general_model)
            self.cursor.execute("SELECT genre from genre")
            result = self.cursor.fetchall()
            self.image.set_from_file("ui/movies.png")
            pixbuf = self.image.get_pixbuf()
            for genre in result:
                self.general_model.append([pixbuf, genre[0]])
        elif headers.get_current_page() == 2:
            self.latest_dict = {}
            self.general_model.clear()
            self.cursor.execute("SELECT value from config where key='series_duration'")
            duration = self.cursor.fetchone()
            week = datetime.now() - timedelta(days=int(duration[0]))
            self.cursor.execute("SELECT episode_name,episode_link,path from episodes join series_images on episodes.series_id=series_images.series_id and episodes.Date BETWEEN ? AND ?",(week,datetime.now(),))
            for episode in self.cursor.fetchall():
                util.render_view(self.image,episode[0], self.general_model, episode[2])
                self.latest_dict[episode[0]] = episode[1]
        elif headers.get_current_page() == 3:
            self.general_model.clear()
            self.cursor.execute("SELECT title,current_season,path  from series join series_images on series.id=series_images.series_id and series.status=1 order by title")
            for series in self.cursor.fetchall():
                util.render_view(self.image, series[0]+" "+"Season"+" "+str(series[1]),
                                  self.general_model,series[2])
        elif headers.get_current_page() == 4:
            self.general_model.clear()
            self.cursor.execute("SELECT title,path  from series join series_images on series.id=series_images.series_id order by title")
            for all_series in self.cursor.fetchall():
                util.render_view(self.image, all_series[0], self.general_model,
                                 all_series[1])

    def on_GenreIcon_activated(self, widget, event):
        choice = util.get_selection(self.genre_icon_view, self.general_model)
        if re.search(r'\(\d+\)$', choice):
            util.open_page(self.cursor, choice,"movie")
        else:
            self.cursor.execute("SELECT id from genre where genre=?",
                                (choice,))
            genre_key = self.cursor.fetchone()
            self.cursor.execute("SELECT title,path from movies join movie_images on  movies.id=movie_images.movie_id and  movies.genre_id=?", (genre_key[0],))
            movie_info = self.cursor.fetchall()
            self.general_model.clear()
            for results in movie_info:
                util.render_view(self.image, results[0],
                                 self.general_model, results[1])

    def on_LatestMovie_activated(self, widget, event):
        latest_movie_view = self.builder.get_object("LatestMovie")
        latest_movie = util.get_selection(latest_movie_view, self.general_model)
        util.open_page(self.cursor, latest_movie, "movie")

    def on_LatestEpisodes_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            path = self.latest_episodes_view.get_path_at_pos(event.x, event.y)
            if path != None:
                self.latest_episodes_view.select_path(path)
                episode = util.get_selection(self.latest_episodes_view,
                                             self.general_model)
                if event.button == 3:
                    self.torrent.query(episode)
                    self.builder.get_object("torrents").popup(None, None, None, None,
                                                       event.button, event.time)
                elif event.button == 1:
                    self.on_LatestEpisodes_activated(widget, episode)

    def on_LatestEpisodes_activated(self, widget, episode):
        util.open_page(self.cursor, self.latest_dict[episode])

    def on_ActiveSeries_activated(self, widget, active_series):
        if re.search(r'^Episode', active_series):
            util.open_page(self.cursor, self.active_series_dic[active_series])
        else:
            self.active_series_dic = {}
            series_name = active_series.split(" Season")[0]
            logging.debug(series_name)
            series_number = active_series.split("Season ")[1]
            logging.debug(series_number)
            self.cursor.execute("SELECT episode_name,episode_link FROM episodes WHERE"+
                        ' series_id=(SELECT id from series where title=?)'+
                        ' and episode_link LIKE ?',
                        (series_name, "%season-"+series_number+"%",))
            self.general_model.clear()
            for current_season in self.cursor.fetchall():
                util.render_view(self.image, current_season[0], self.general_model)
                self.active_series_dic[current_season[0]] = current_season[1]

    def on_ActiveSeries_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            path = self.active_series_view.get_path_at_pos(event.x, event.y)
            if path != None:
                self.active_series_view.select_path(path)
                series = util.get_selection(self.active_series_view,self.general_model)
                self.striped_name = series.split(" Season")[0]
                if event.button == 3:
                    self.builder.get_object("Series").popup(None, None, None, None,
                                                            event.button, event.time)
                elif event.button == 1:
                    self.on_ActiveSeries_activated(widget, series)

    def on_SeriesArchive_activated(self, widget, event):
        series_archive_view = self.builder.get_object("SeriesArchive")
        choice = util.get_selection(series_archive_view,self.general_model)
        if re.search(r'^Season', choice):
            self.archive_series_dict = {}
            logging.debug("Season selected")
            no = choice.split("Season ")[1]
            self.cursor.execute("SELECT episode_name,episode_link FROM episodes" +
                                ' WHERE series_id=(SELECT id from series where title=?)' +
                                ' and episode_link LIKE ?',
                                (self.series_name, "%season-"+ no +"%",))
            self.general_model.clear()
            for current_season in self.cursor.fetchall():
                util.render_view(self.image, current_season[0], self.general_model)
                self.archive_series_dict[current_season[0]] = current_season[1]
        elif re.search(r'^Episode', choice):
            util.open_page(self.cursor, self.archive_series_dict[choice])
        else:
            self.series_name = choice
            logging.debug("series selected %s" %choice)
            self.cursor.execute("SELECT number_of_seasons from series where title=?",
                                (choice,))
            no_seasons = self.cursor.fetchone()
            index = 1
            self.general_model.clear()
            while index <= int(no_seasons[0]):
                util.render_view(self.image, "Season %s" % index, self.general_model)
                index += 1

    def on_AddSeries_activate(self, widget):
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

    def on_poster_update_activate(self, widget):
        "New thread to fetch  Images"
        self.fetch = FetchPosters(self.db_file)
        self.fetch.setDaemon(True)
        self.fetch.start()

