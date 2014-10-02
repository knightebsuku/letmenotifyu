import sqlite3
import re
import logging

from datetime import datetime, timedelta
from gi.repository import Gtk, GObject
from notifylib.gui import Add_Series, About, Confirm, Statistics, Preferences, Current_Season
from notifylib.torrent import Torrent
from notifylib import util
from notifylib.check_updates import UpdateClass

GObject.threads_init()


class Main:
    def __init__(self, gladefile, db):
        self.connect = sqlite3.connect(db)
        self.cursor = self.connect.cursor()
        self.db_file = db
        self.builder = Gtk.Builder()
        self.image = Gtk.Image()
        self.builder.add_from_file(gladefile)
        signals = {'on_AppWindow_destroy': Gtk.main_quit,
                   'on_headers_event': self.on_headers_event,
                   'on_GenreIcon_activated': self.on_GenreIcon_activated,
                   'on_LatestMovie_activated': self.on_LatestMovie_activated,
                   'on_LatestEpisodesIcon_activated': self.on_LatestEpisodes_activated,
                   'on_ActiveSeries_activated': self.on_ActiveSeries_activated,
                   'on_SeriesArchive_activated': self.on_SeriesArchive_activated}
                   #'on_AddSeries_activate': self.on_AddSeries_activate,
                   #'on_Quit_activate': Gtk.main_quit,
                   #'on_About_activate': self.on_About_activate,}
        ## signals = {'on_winlet_destroy': self.on_winlet_destroy,
        ##          'on_ViewMovies': self.on_ViewMovies,
        ##          'on_ViewCurrentSeries': self.on_ViewCurrentSeries,
        ##          'on_ViewLatestSeries': self.on_ViewLatestSeries,
        ##          'on_ViewSeriesArchive': self.on_ViewSeriesArchive,
        ##          'on_Stop_Update_activate': self.on_Stop_Update_activate,
        ##          'on_Start_Update_activate': self.on_Start_Update_activate,
        ##          'on_Delete_Series_activate': self.on_Delete_Series_activate,
        ##          'on_Properties_activate': self.on_Properties_activate,
        ##          'on_Kickass_activate': self.on_Kickass_activate,
        ##          'on_Piratebay_activate': self.on_Piratebay_activate,
        ##          'on_online_video_activate': self.on_online_video_activate,
        ##          'on_pref_activate': self.on_pref_activate,
        ##          'on_Current_Season_activate': self.on_Current_Season_activate}

        self.builder.connect_signals(signals)
        self.general_model = self.builder.get_object("General")
        self.genre_icon_view = self.builder.get_object("GenreIcon")
        self.latest_episodes_view = self.builder.get_object("LatestEpisodesIcon")
        self.builder.get_object('AppWindow').show()
        #update = UpdateClass(self.db_file)
        #update.setDaemon(True)
        #update.start()
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
                self.image.set_from_file(movie[1])
                pixbuf = self.image.get_pixbuf()
                self.general_model.append([pixbuf, movie[0]])
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
                self.image.set_from_file(episode[2])
                pixbuf = self.image.get_pixbuf()
                self.general_model.append([pixbuf, episode[0]])
                self.latest_dict[episode[0]] = episode[1]
        elif headers.get_current_page() == 3:
            logging.debug("Active Series Clicked")
            self.general_model.clear()
            self.cursor.execute("SELECT title,current_season,path  from series join series_images on series.id=series_images.series_id and series.status=1 order by title")
            for series in self.cursor.fetchall():
                self.image.set_from_file(series[2])
                pixbuf = self.image.get_pixbuf()
                self.general_model.append([pixbuf, series[0]+" "+"Season"+" "+str(series[1])])
        elif headers.get_current_page() == 4:
            self.general_model.clear()
            self.cursor.execute("SELECT title,path  from series join series_images on series.id=series_images.series_id order by title")
            for all_series in self.cursor.fetchall():
                self.image.set_from_file(all_series[1])
                pixbuf = self.image.get_pixbuf()
                self.general_model.append([pixbuf, all_series[0]])

    def on_GenreIcon_activated(self, widget, event):
        choice = util.get_selection(self.genre_icon_view, self.general_model)
        if re.search(r'\(\d+\)$', choice):
            util.open_page(self.cursor, choice,"movie")
        else:
            self.cursor.execute("SELECT id from genre where genre=?",
                                (choice,))
            genre_key = self.cursor.fetchone()
            self.cursor.execute("SELECT title,path from movies join movie_images on  movies.id=movie_images.movie_id and  movies.genre_id=?",(genre_key[0],))
            movie_info = self.cursor.fetchall()
            self.general_model.clear()
            for results in movie_info:
                self.image.set_from_file(results[1])
                poster = self.image.get_pixbuf()
                self.general_model.append([poster, results[0]])
        

    def on_LatestMovie_activated(self, widget, event):
        latest_movie_view = self.builder.get_object("LatestMovie")
        latest_movie = util.get_selection(latest_movie_view, self.general_model)
        util.open_page(self.cursor, latest_movie, "movie")

    def on_LatestEpisodes_activated(self, *args):
        latest_episode_view = self.builder.get_object("LatestEpisodesIcon")
        latest_episode = util.get_selection(latest_episode_view, self.general_model)
        util.open_page(self.cursor, self.latest_dict[latest_episode])

    def on_ActiveSeries_activated(self,*args):
        active_series_view = self.builder.get_object("ActiveSeries")
        active_series = util.get_selection(active_series_view, self.general_model)
        if re.search(r'^Episode',active_series):
            util.open_page(self.cursor, self.active_series_dic[active_series])
        else:
            self.active_series_dic = {}
            logging.debug("%s selected" % active_series)
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
                self.image.set_from_file("ui/movies.png")
                pixbuf = self.image.get_pixbuf()
                self.general_model.append([pixbuf, current_season[0]])
                self.active_series_dic[current_season[0]] = current_season[1]

    def on_SeriesArchive_activated(self,*args):
        self.archive_series_dict = {}
        series_archive_view = self.builder.get_object("SeriesArchive")
        choice = util.get_selection(series_archive_view,self.general_model)
        if re.search(r'^Season', choice):
            logging.debug("Season selected")
            no = choice.split("Season ")[1]
            self.cursor.execute("SELECT episode_name,episode_link FROM episodes" +
                                ' WHERE series_id=(SELECT id from series where title=?)' +
                                ' and episode_link LIKE ?',
                                (self.series_name, "%season-"+ no +"%",))
            self.general_model.clear()
            for current_season in self.cursor.fetchall():
                self.image.set_from_file("ui/movies.png")
                pixbuf = self.image.get_pixbuf()
                self.general_model.append([pixbuf, current_season[0]])
                self.archive_series_dict[current_season[0]] = current_season[1]
        else:
            self.series_name = choice
            logging.debug("series selected %s" %choice)
            self.cursor.execute("SELECT number_of_seasons from series where title=?",
                                (choice,))
            no_seasons = self.cursor.fetchone()
            index = 1
            self.general_model.clear()
            while index <= int(no_seasons[0]):
                self.image.set_from_file("ui/movies.png")
                pixbuf = self.image.get_pixbuf()
                self.general_model.append([pixbuf,"Season %s" % index])
                index += 1

    def on_AddSeries_activate(self, widget):
        Add_Series('ui/add_series.glade', self.cursor, self.connect)

    def on_About_activate(self, widget):
        About('ui/about.glade')

    def on_ViewLatestSeries(self, widget, event):
            self.torrent = Torrent(self.get_episode, self.cursor)
            self.builder.get_object("torrents").popup(None, None, None, None,
                                                       event.button, event.time)

    def on_Piratebay_activate(self, widget):
        self.torrent.piratebay()

    def on_Kickass_activate(self, widget):
        self.torrent.kickass()

    def on_online_video_activate(self, widget):
        self.torrent.online(self.latest_dict)
   
    def on_Stop_Update_activate(self, widget):
        Confirm('confirm.glade', self.series_title, "stop", self.connect, self.cursor)

    def on_Start_Update_activate(self, widget):
        Confirm('confirm.glade', self.series_title, "start", self.connect, self.cursor)

    def on_Delete_Series_activate(self, widget):
        Confirm('confirm.glade', self.series_title, "delete", self.connect, self.cursor)

    def on_Properties_activate(self, widget):
        Statistics('stats.glade', self.series_title, self.connect, self.cursor)

    def on_pref_activate(self, widget):
        Preferences('preferences.glade',self.cursor, self.connect,
                    self.update, self.db_file)

    def on_Current_Season_activate(self, widget):
        Current_Season("set_season.glade", self.cursor, self.connect, self.series_title)
