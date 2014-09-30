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
                   'on_AddSeries_activate': self.on_AddSeries_activate,
                   'on_Quit_activate': Gtk.main_quit,
                   'on_About_activate': self.on_About_activate,}
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
        self.latest_series_view = self.builder.get_object("LatestSeriesIcon")
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
            self.general_model.clear()
            #self.latest_series_view.set_model(self.general_model)
            self.cursor.execute("SELECT value from config where key='series_duration'")
            duration = self.cursor.fetchone()
            week = datetime.now() - timedelta(days=int(duration[0]))
            self.cursor.execute("SELECT episode_name,episode_link,path from episodes join series_images on episodes.series_id=series_images.series_id and episodes.Date BETWEEN ? AND ?",(week,datetime.now(),))
            for episode in self.cursor.fetchall():
                self.image.set_from_file(episode[2])
                pixbuf = self.image.get_pixbuf()
                self.general_model.append([pixbuf, episode[0]])

    def on_GenreIcon_activated(self, widget, event):
        selection_tree_path = self.genre_icon_view.get_selected_items()
        selection_iter = self.general_model.get_iter(selection_tree_path)
        model = self.genre_icon_view.get_model()
        choice = model.get_value(selection_iter, 1)
        if re.search(r'\(\d+\)$', choice):
            util.open_page(self.cursor, choice)
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
        latest_tree_path = latest_movie_view.get_selected_items()
        latest_iter = self.general_model.get_iter(latest_tree_path)
        model = latest_movie_view.get_model()
        latest_movie = model.get_value(latest_iter, 1)
        util.open_page(self.cursor, latest_movie)

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

    def on_ViewCurrentSeries(self, widget, event):
        if event.button == 1:
            selected = self.view_current_series.get_selection()
            series, name = selected.get_selected()
            episode = series[name][0]
            if re.match(r"^Episode", episode):
                path = self.store_current_series.get_path(name)
                path_value = str(path).split(":")

                episode_title_path = self.store_current_series.get_iter(path_value[0])
                episode_season_path = self.store_current_series.get_iter(path_value[0] +
                                                                         ":"+path_value[1])
                episode_path = self.store_current_series.get_iter(path_value[0] + ":" +
                                                            path_value[1]+":"+path_value[2])

                model = self.view_current_series.get_model()
                episode_title = model.get_value(episode_title_path, 0)
                episode_season = model.get_value(episode_season_path, 0)
                episode = model.get_value(episode_path, 0)
                sql_season = episode_season.replace(" ", "-")

                self.cursor.execute("SELECT episode_link FROM episodes WHERE episode_name=? AND title=? AND episode_link LIKE ?",
                                    (episode, episode_title, "%"+sql_season+"%"))
                link = self.cursor.fetchone()
                webbrowser.open_new("http://www.primewire.ag"+link[0])
                logging.info("Opening Link: "+link[0])
            else:
                pass
        elif event.button == 3:
            selected = self.view_current_series.get_selection()
            series, name = selected.get_selected()
            self.series_title = series[name][0]
            if not re.match(r"^Episode",self.series_title) or re.match(r'^season',
                                                                               self.series_title):
                title = self.store_current_series.get_path(name)
                try:
                    int(str(title))
                    self.builder.get_object("Series").popup(None, None, None, None,
                                                        event.button, event.time)
                except ValueError as e:
                    logging.warn(e)
                    pass


    def on_ViewSeriesArchive(self, widget, event):
        if event.button == 1:
            selected = self.view_series_archive.get_selection()
            series, name = selected.get_selected()
            episode = series[name][0]
            if re.match(r"^Episode", episode):
                path = self.store_series_archive.get_path(name)
                path_value = str(path).split(":")
                episode_title_path = self.store_series_archive.get_iter(path_value[0])
                episode_season_path = self.store_series_archive.get_iter(path_value[0]+
                                                                         ":"+path_value[1])
                episode_path = self.store_series_archive.get_iter(path_value[0]+":"+
                                                            path_value[1]+":"+path_value[2])

                model = self.view_series_archive.get_model()
                episode_title = model.get_value(episode_title_path, 0)
                episode_season = model.get_value(episode_season_path, 0)
                episode = model.get_value(episode_path, 0)
                sql_season = episode_season.replace(" ", "-")

                self.cursor.execute("SELECT episode_link FROM episodes WHERE episode_name=? AND title=? AND episode_link LIKE ?",
                                    (episode, episode_title, "%"+sql_season+"%"))
                link = self.cursor.fetchone()
                webbrowser.open_new("http://www.primewire.ag"+link[0])
                logging.info("Opening Link"+link[0])
            else:
                pass
        elif event.button == 3:
            selected = self.view_series_archive.get_selection()
            series, name = selected.get_selected()
            self.series_title = series[name][0]
            if not re.match(r"^Episode",self.series_title) or re.match(r'^season',
                                                                               self.series_title):
                title = self.store_series_archive.get_path(name)
                try:
                    int(str(title))
                    self.builder.get_object("Series").popup(None, None, None, None,
                                                        event.button, event.time)
                except ValueError as e:
                    logging.warn(e)
                    pass

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

    def on_notebook1(self, widget, event):
        if self.notebook1.get_current_page() == 0:
            query = "SELECT Id,genre FROM genre"
            create_category(self.cursor, self.store_movies, query)
        elif self.notebook1.get_current_page() == 1:
            self.store_current_series.clear()
            query = "SELECT title,current_season from series where status=1 order by title"
            create_current_parent(self.cursor, self.store_current_series, query)
        elif self.notebook1.get_current_page() == 2:
            week = datetime.now() - timedelta(days=7)
            self.builder.get_object('listLatestSeries').clear()
            self.cursor.execute('SELECT title,episode_link,episode_name FROM episodes WHERE Date BETWEEN  ? AND ? order by title',
                                (week, datetime.now()))
            for latest in self.cursor.fetchall():
                self.latest_dict[latest[0]+"-"+latest[2]] = "http://www.primewire.ag"+latest[1]
                self.builder.get_object('listLatestSeries').append([latest[0]+"-"+latest[2]])

        elif self.notebook1.get_current_page() == 3:
            self.store_series_archive.clear()
            query = "SELECT title,number_of_seasons from series order by title"
            create_parent(self.cursor, self.store_series_archive, query)
        else:
            pass


