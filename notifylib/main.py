import sqlite3
import webbrowser
import re
import logging

from datetime import datetime, timedelta
from gi.repository import Gtk, GObject
from notifylib.gui import Add_Series, About, Confirm, Statistics, Preferences, Current_Season
from notifylib.torrent import Torrent
from notifylib.check_updates import UpdateClass

GObject.threads_init()


class Main:
    def __init__(self, gladefile, pic, db):
        self.connect = sqlite3.connect(db)
        self.cursor = self.connect.cursor()
        self.db_file = db
        self.latest_dict = {}
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        signals = {'on_winlet_destroy': self.on_winlet_destroy,
                 'on_imageAdd_activate': self.on_imageAdd_activate,
                 'on_imageQuit_activate': self.on_imageQuit_activate,
                 'on_imageAbout_activate': self.on_imageAbout_activate,
                 'on_notebook1': self.on_notebook1,
                 'on_ViewMovies': self.on_ViewMovies,
                 'on_ViewCurrentSeries': self.on_ViewCurrentSeries,
                 'on_ViewLatestSeries': self.on_ViewLatestSeries,
                 'on_ViewSeriesArchive': self.on_ViewSeriesArchive,
                 'on_Stop_Update_activate': self.on_Stop_Update_activate,
                 'on_Start_Update_activate': self.on_Start_Update_activate,
                 'on_Delete_Series_activate': self.on_Delete_Series_activate,
                 'on_Properties_activate': self.on_Properties_activate,
                 'on_Isohunt_activate': self.on_Isohunt_activate,
                 'on_Kickass_activate': self.on_Kickass_activate,
                 'on_Piratebay_activate': self.on_Piratebay_activate,
                 'on_online_video_activate': self.on_online_video_activate,
                 'on_pref_activate': self.on_pref_activate,
                 'on_Current_Season_activate': self.on_Current_Season_activate}

        self.builder.connect_signals(signals)
        self.view_series_archive = self.builder.get_object('ViewSeriesArchive')
        self.view_current_series = self.builder.get_object('ViewCurrentSeries')
        self.store_current_series = self.builder.get_object('StoreCurrentSeries')
        self.store_series_archive = self.builder.get_object('StoreSeriesArchive')
        self.store_movies = self.builder.get_object("StoreMovies")
        self.view_movies = self.builder.get_object("ViewMovies")
        self.notebook1 = self.builder.get_object('notebook1')
        self.window = self.builder.get_object('winlet').show()
        self.update = UpdateClass(self.db_file)
        self.update.setDaemon(True)
        self.update.start()
        Gtk.main()

    def on_winlet_destroy(self, widget):
        Gtk.main_quit()

    def on_imageAdd_activate(self, widget):
        Add_Series('add_series.glade', self.cursor, self.connect)

    def on_imageQuit_activate(self, widget):
        self.on_winlet_destroy(widget)

    def on_imageAbout_activate(self, widget):
        About('about.glade')

    def on_ViewMovies(self, widget, event):
        if event.button == 1:
            try:
                get_title = self.builder.get_object("ViewMovies").get_selection()
                movie, name = get_title.get_selected()
                fetch_title = movie[name][0]
                self.cursor.execute("SELECT link FROM movies WHERE title=?",
                                (fetch_title,))
                link = self.cursor.fetchone()
                webbrowser.open_new("http://www.primewire.ag"+link[0])
                logging.info("Opening Link:"+link[0])
            except TypeError:
                pass

    def on_ViewLatestSeries(self, widget, event):
        if event.button == 3:
            get_latest_series = self.builder.get_object("ViewLatestSeries").get_selection()
            latest, name = get_latest_series.get_selected()
            self.get_episode = latest[name][0]
            self.torrent = Torrent(self.get_episode, self.cursor, self.connect)
            self.builder.get_object("torrents").popup(None, None, None, None,
                                                       event.button, event.time)

    def on_Isohunt_activate(self, widget):
        self.torrent.isohunt()

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
            self.store_movies.clear()
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


#Movie list creation
def create_category(cursor, store_movies, query):
    cursor.execute(query)
    for results in cursor.fetchall():
        category = store_movies.append(None, [results[1]])
        add_movies(cursor, results[0],category, store_movies)

        
def add_movies(cursor, id, category, store_movies):
    cursor.execute("SELECT title from movies where genre_Id=?",(id,))
    for movie in cursor.fetchall():
        store_movies.append(category, [movie[0]])


#Latest Series list creation
def create_current_parent(cursor, series_column, query):
    cursor.execute(query)
    for results in cursor.fetchall():
        parent_title = series_column.append(None, [results[0]])
        create_current_episodes(cursor, results[0], parent_title, series_column, results[1])

        
def create_current_episodes(cursor, series_title, parent_title,
                            series_column, current_season):
    name = "season " + str(current_season)
    sql_name = "%season-"+str(current_season)+"%"
    series_number = series_column.append(parent_title, [name])
    cursor.execute("SELECT episode_name FROM episodes WHERE title=? and episode_link LIKE ?",
                   (series_title, sql_name))
    for episode in cursor.fetchall():
        series_column.append(series_number, [episode[0]])

        
#Series archive creation
def create_parent(cursor, series_column, query):
    x = 1
    cursor.execute(query)
    for results in cursor.fetchall():
        parent_title = series_column.append(None, [results[0]])
        while x <= int(results[1]):
            create_episodes(cursor, results[0], parent_title, series_column, x)
            x += 1
        x = 1

        
def create_episodes(cursor, series_title, parent_title, series_column, x):
    name = "season "+str(x)
    sql_name = "%season-"+str(x)+"-%"
    series_number = series_column.append(parent_title, [name])
    cursor.execute("SELECT episode_name FROM episodes WHERE title=? and episode_link LIKE ?",
                   (series_title, sql_name))
    for episode in cursor.fetchall():
        series_column.append(series_number, [episode[0]])
