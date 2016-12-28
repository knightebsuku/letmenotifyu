#!/usr/bin/python3

import psycopg2
import sqlite3
import logging

from datetime import datetime, timedelta
from . import gui, util, settings
from . import background_worker as bw

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')

from gi.repository import Gtk, Gdk


log = logging.getLogger(__name__)


class Main(object):
    "Main application"
    def __init__(self):
        self.movie_connect = sqlite3.connect(settings.MOVIE_DB)
        self.movie_cursor = self.movie_connect.cursor()
        self.series_connect = sqlite3.connect(settings.SERIES_DB)
        self.series_cursor = self.series_connect.cursor()
        self.movie_cursor.execute(settings.SQLITE_WAL_MODE)
        self.series_cursor.execute(settings.SQLITE_WAL_MODE)

        self.builder = Gtk.Builder()
        self.image = Gtk.Image()
        self.view_flag = ""
        self.episodes_dict = {}
        self.builder.add_from_file("ui/Main.glade")
        signals = {'on_AppWindow_destroy': self.on_quit,
                   'on_HeaderView_event': self.header_view_event,
                   'on_GeneralIconView_activated': self.general_view_activate,
                   'on_GeneralIconView_event': self.general_view_event,
                   'on_SeriesPeferencesMenuItem_activate': self.series_preference,
                   'on_AddSeriesMenuItem_activate': self.add_series_activate,
                   'on_MovePeferencesMenuItem_activate': self.movie_preference,
                   'on_GeneralPreference_activate': self.pref_activate,
                   'on_Stop_Update_activate': self.stop_update_activate,
                   'on_Start_Update_activate': self.start_update_activate,
                   'on_Delete_Series_activate': self.delete_series_activate,
                   'on_preferences_activate': self.pref_activate,
                   'on_Quit_activate': self.on_quit,
                   'on_About_activate': self.about_activate,
                   'on_BtnRoot_clicked': self.button_root_clicked,
                   'on_BtnLevel1_clicked': self.button_one_clicked,
                   'on_BtnLevel2_clicked': self.button_two_clicked,
                   'on_series_watch_activate': self.series_watch,
                   'on_watchlist_activate': self.watch_list,
                   'on_ViewOnline_activate': self.view_episode_online,
                   'on_AddEpisodeQueue_activate': self.add_episode_queue}

        self.builder.connect_signals(signals)
        self.header_dic = {
            'Released Movies': self.released_movies_view_selected,
            'Movie Archive': self.movie_archive_view_selected,
            'Latest Episodes': self.latest_episodes_view_selected,
            'Series on Air': self.series_on_air_view_selected,
            'Series Archive': self.series_archive_view_selected,
            'Movie Queue': self.watch_queue_movie_selected,
            'Series Queue': self.watch_queue_series_selected}
        self.general_model = self.builder.get_object("General")
        self.general_icon_view = self.builder.get_object('GeneralIconView')
        self.button_level_1 = self.builder.get_object("BtnLevel1")
        self.button_level_2 = self.builder.get_object("BtnLevel2")
        util.pre_populate_menu(self.builder)
        self.builder.get_object('AppWindow').show()
        # self.sp = sp
        # self.mp = mp
        # self.mdp = mdp
        #bw.start_threads()
        Gtk.main()

    def on_quit(self, widget):
        self.movie_connect.close()
        self.series_connect.close()
        log.debug("Shutting down processes")
        # self.sp.terminate()
        # self.mp.terminate()
        # self.mdp.terminate()
        Gtk.main_quit()

    def general_view_activate(self, widget, choice):
        if self.view_flag == "latest_episode_view_selected":
            util.open_page(self.series_cursor, self.episodes_dict[choice])
        elif self.view_flag == "released_movies_view_selected":
            gui.MovieDetails(self.movie_cursor, self.movie_connect, choice)
        elif self.view_flag == "movie_archive_view_selected":
            self.movie_archive_view_genre_selected(choice)
            self.button_level_1.set_property("visible", True)
            self.button_level_1.set_property("label", choice)
        elif self.view_flag == "movie_archive_view_genre_selected":
            gui.MovieDetails(self.movie_cursor, self.movie_connect, choice)
        elif self.view_flag == "series_on_air_view_selected":
            self.series_on_air_view_series_selected(choice)
            self.button_level_1.set_property("visible", True)
            self.button_level_1.set_property("label", choice)
        elif self.view_flag == "series_archive_view_selected":
            self.series_archive_view_season_selected(choice)
            self.button_level_1.set_property("visible", True)
            self.button_level_1.set_property("label", choice)
        elif self.view_flag == "series_archive_view_season_selected":
            self.series_archive_view_season_episode_view_selected(choice)
            self.button_level_2.set_property("visible", True)
            self.button_level_2.set_property("label", choice)
        
    def general_view_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            path = widget.get_path_at_pos(event.x, event.y)
            if path:
                widget.select_path(path)
                self.choice = util.get_selection(widget, self.general_model)
                self.striped_name = self.choice.split(" Season")[0]
                if event.button == 1:
                    self.general_view_activate(widget, self.choice)
                elif event.button == 3 and self.view_flag == "series_archive_view_selected":
                    self.builder.get_object("Series").popup(None, None, None, None,
                                                            event.button, event.time)
                elif event.button == 3 and self.view_flag == "series_on_air_view_selected":
                    self.builder.get_object("Series").popup(None, None, None, None,
                                                            event.button, event.time)
                elif event.button == 3 and self.view_flag == "watch series":
                    self.builder.get_object("RemoveQueue").popup(None, None, None, None,
                                                                 event.button, event.time)
                elif event.button == 3 and self.view_flag == "series_on_air_view_series_selected":
                    self.builder.get_object("Episode").popup(None, None, None, None,
                                                             event.button, event.time)
                elif event.button == 3 and self.view_flag == 'series_archive_view_season_episode_view_selected':
                    self.builder.get_object("Episode").popup(None, None, None, None,
                                                             event.button, event.time)

    def header_view_event(self, widget, event):
        "selection of header"
        button_root = self.builder.get_object("BtnRoot")
        if event.button == 1:
            selection = widget.get_selection()
            name, itr = selection.get_selected()
            header_choice = name[itr][0]
            try:
                self.image.clear()
                self.header_dic[header_choice]()
                button_root.set_property("label", header_choice)
                button_root.set_property("visible", True)
                self.button_level_1.set_property("visible", False)
                self.button_level_2.set_property("visible", False)
            except KeyError:
                pass

    def released_movies_view_selected(self):
        "show movies which have just been released"
        self.general_model.clear()
        self.movie_cursor.execute("SELECT value FROM config "
                                  "WHERE key='movie_duration'")
        duration = self.movie_cursor.fetchone()
        week = datetime.now() - timedelta(days=float(duration[0]))
        self.movie_cursor.execute("SELECT title, path from movies "
                                  "JOIN movie_images "
                                  "ON movies.id=movie_images.movie_id "
                                  "AND date_added BETWEEN ? AND ?",
                                  (week, datetime.now(),))
        for (title, path) in self.movie_cursor.fetchall():
            util.render_view(self.image, title, self.general_model,
                             path)
        self.view_flag = "released_movies_view_selected"

    def movie_archive_view_genre_selected(self, choice):
        "show all movies from a particular genre"
        self.movie_cursor.execute("SELECT id FROM genre WHERE genre=?",
                                  (choice,))
        self.search_choice = choice
        (genre_key,) = self.movie_cursor.fetchone()
        self.movie_cursor.execute('SELECT title,path FROM movies '
                                  "JOIN movie_images ON "
                                  "movies.id=movie_images.movie_id "
                                  'AND genre_id=? '
                                  'order by title', (genre_key,))
        movie_info = self.movie_cursor.fetchall()
        self.general_model.clear()
        for (movie_title, path) in movie_info:
            util.render_view(self.image, movie_title,
                             self.general_model, path)
        self.view_flag = "movie_archive_view_genre_selected"

    def series_on_air_view_series_selected(self, choice):
        "show current seasons episodes"
        self.episodes_dict = {}
        series_name = choice.split(" Season")[0]
        log.debug(series_name)
        series_number = choice.split("Season ")[1]
        log.debug(series_number)
        self.series_cursor.execute("SELECT episode_number||episode_name,"
                                   "episode_link "
                                   "FROM episodes e JOIN "
                                   "series s "
                                   "ON e.series_id=s.id "
                                   "AND episode_link LIKE ?",
                                   ("%season-{}%".format(series_number),))
        # self.series_cursor.execute("SELECT episode_number || episode_name,"
        #                            "episode_link "
        #                            "FROM episodes WHERE "
        #                            'series_id=(SELECT id from series where title=?) '
        #                            'and episode_link LIKE ?',
        #                            (series_name, "%season-{}%".format(series_number),))
        self.general_model.clear()
        for (episode_name, episode_link) in self.series_cursor.fetchall():
            util.render_view(self.image, episode_name, self.general_model)
            self.episodes_dict[episode_name] = episode_link
        self.view_flag = "series_on_air_view_series_selected"

    def movie_archive_view_selected(self):
        "show all movie genres"
        self.general_model.clear()
        self.movie_cursor.execute("SELECT genre FROM genre ORDER BY genre")
        result = self.movie_cursor.fetchall()
        for genre in result:
            self.image.set_from_file("icons/"+genre[0]+'.png')
            pixbuf = self.image.get_pixbuf()
            self.general_model.append([pixbuf, genre[0]])
        self.view_flag = "movie_archive_view_selected"

    def latest_episodes_view_selected(self):
        "show latest episodes"
        self.episodes_dict = {}
        self.general_model.clear()
        self.series_cursor.execute("SELECT value FROM config "
                                   "WHERE key='series_duration'")
        duration = self.series_cursor.fetchone()
        week = datetime.now() - timedelta(days=float(duration[0]))
        self.series_cursor.execute("SELECT episode_number||episode_name,"
                                   "episode_link,path FROM episodes e "
                                   "JOIN series_images si "
                                   "ON e.series_id=si.series_id "
                                   "AND date BETWEEN ? AND ?",
                                   (week, datetime.now(),))
        for (episode_name, episode_link, path) in self.series_cursor.fetchall():
            util.render_view(self.image, episode_name, self.general_model,
                             path)
            self.episodes_dict[episode_name] = episode_link
        self.view_flag = 'latest_episode_view_selected'

    def series_on_air_view_selected(self):
        "show series which are currently on air"
        self.general_model.clear()
        self.series_cursor.execute("SELECT title,number_of_seasons,path "
                                   "FROM series "
                                   "JOIN series_images "
                                   "ON series.id=series_id "
                                   "AND status='t' ORDER BY title")
        for (title, current_season, path) in self.series_cursor.fetchall():
            full_title = title+" "+"Season"+" "+str(current_season)
            util.render_view(self.image, full_title,
                             self.general_model, path)
        self.view_flag = 'series_on_air_view_selected'

    def series_archive_view_selected(self):
        "show all series"
        self.general_model.clear()
        self.series_cursor.execute("SELECT title,path FROM series "
                                   "JOIN series_images "
                                   "ON series.id=series_images.series_id "
                                   "ORDER BY title")
        for (title, path) in self.series_cursor.fetchall():
            util.render_view(self.image, title, self.general_model, path)
            self.view_flag = 'series_archive_view_selected'

    def series_archive_view_season_selected(self, choice):
        "show seasons of series"
        self.series_name = choice
        self.series_cursor.execute("SELECT number_of_seasons "
                                   "FROM series WHERE title=?",
                                   (choice,))
        (no_seasons,) = self.series_cursor.fetchone()
        self.general_model.clear()
        for num in range(1, no_seasons+1):
            util.render_view(self.image, "Season {}".format(num),
                             self.general_model)
        self.view_flag = "series_archive_view_season_selected"

    def series_archive_view_season_episode_view_selected(self, choice):
        "show episodes of particular season of a series"
        self.episodes_dict = {}
        no = choice.split("Season ")[1]
        self.series_cursor.execute("SELECT episode_number || episode_name,"
                                   "episode_link"
                                   "FROM episodes e "
                                   "JOIN series s "
                                   "ON e.series_id=s.id "
                                   "AND episode_link LIKE ? ",
                                   (self.series_name,
                                    "%season-" + no + "%"))
        # self.series_cursor.execute("SELECT episode_number || episode_name,"
        #                            "episode_link FROM episodes "
        #                            'WHERE series_id=(SELECT id from series where title=%s) ' \
        #                     ' and episode_link LIKE %s',
        #                     (self.series_name, "%season-" + no + "%",))
        self.general_model.clear()
        for (episode_name, episode_link) in self.series_cursor.fetchall():
            util.render_view(self.image, episode_name, self.general_model)
            self.episodes_dict[episode_name] = episode_link
        self.view_flag = "series_archive_view_season_episode_view_selected"

    def watch_queue_movie_selected(self):
        "show movies in queue"
        self.general_model.clear()
        self.movie_cursor.execute("SELECT mi.path, wqs.name FROM "
                                  "movie_images mi, watch_queue_status wqs "
                                  "JOIN movie_queue mq ON mq.id=mi.id "
                                  "AND wqs.id=mq.watch_queue_status_id;")
        for (path, watch_name) in self.movie_cursor.fetchall():
            util.render_view(self.image, watch_name, self.general_model,
                             path)
        self.view_flag = 'watch_queue_movies_selected'

    def watch_queue_series_selected(self):
        "show series in watch queue"
        self.general_model.clear()
        self.series_cursor.execute("SELECT si.path,wqs.name,sq.episode_name "
                                   "FROM series_images si,"
                                   'watch_queue_status wqs,'
                                   'series_queue sq '
                                   'WHERE wqs.id=sq.watch_queue_status_id '
                                   'AND sq.series_id=si.series_id '
                                   'ORDER BY sq.id DESC limit 15')
        for (path, watch_name, episode_name) in self.series_cursor.fetchall():
            util.render_view(self.image, episode_name+":  "+watch_name,
                             self.general_model,
                             path)
        self.view_flag = 'watch_queue_series_selected'

    def button_root_clicked(self, widget):
        self.header_dic[widget.get_label()]()

    def button_one_clicked(self, widget):
        if self.view_flag in ("released_movies_view_selected",
                              "movie_archive_view_genre_selected"):
            self.released_movies_select(widget.get_label())
        elif self.view_flag in ("series_on_air_view_selected",
                                "series_on_air_view_series_selected"):
            self.series_on_air_series_selected(widget.get_label())
        elif self.view_flag in ("series_archive_view_season_episode_view_selected", "series_archive_view_selected"):
            self.series_archive_view_season_selected(widget.get_label())

    def button_two_clicked(self, widget):
        self.season__view_selected(widget.get_label())

    def series_preference(self, widget):
        gui.SeriesPreference()

    def add_series_activate(self, widget):
        gui.AddSeries()

    def movie_preference(self, widget):
        gui.MoviePreference()

    def about_activate(self, widget):
        gui.About()

    def stop_update_activate(self, widget):
        gui.Confirm(self.striped_name, "stop", self.connect, self.series_cursor)

    def start_update_activate(self, widget):
        gui.Confirm(self.striped_name, "start", self.connect, self.series_cursor)

    def delete_series_activate(self, widget):
        gui.Confirm(self.striped_name, "delete", self.connect, self.series_cursor)

    def pref_activate(self, widget):
        gui.Preferences()

    def series_watch(self, widget):
        "add series to watch list"
        if self.view_flag == 'series_archive_view_selected':
            try:
                self.series_cursor.execute("UPDATE series SET watch='t' "
                                           "WHERE title=?",
                                           (self.choice,))
                self.connect.commit()
                gui.Error("{} has been added to the watch list".format(self.choice))
            except psycopg2.OperationalError as e:
                log.exception(e)

    def watch_list(self, widget):
        "add movie to watch queue"
        try:
            self.movie_cursor.execute("INSERT INTO movie_queue(movie_id,"
                                      "watch_queue_status_id) "
                                      "SELECT movies.id,watch_queue_status.id "
                                      "FROM movies,watch_queue_status "
                                      "WHERE movies.title=? "
                                      "AND watch_queue_status.name='new'",
                                      (self.choice,))
            self.connect.commit()
            gui.Error("{} has been added to the watch list".format(self.choice))
        except psycopg2.IntegrityError:
            gui.Error("record is already in the movie queue")

    def add_episode_queue(self, widget):
        " add exsisting episode to watch list"
        try:
            self.series_cursor.execute("INSERT INTO series_queue(series_id,"
                                       "episode_id,episode_name) "
                                       "SELECT series_id,id,episode_number "
                                       "FROM episodes WHERE episode_link=?",
                                       (self.episodes_dict[self.choice],))
            self.connect.commit()
            log.info("adding {} to series queue".format(self.episodes_dict[self.choice]))
        except psycopg2.IntegrityError:
            gui.Error("Episode is already in the queue")

    def view_episode_online(self, widget):
        "view episode online"
        util.open_page(self.series_cursor, self.episodes_dict[self.choice])
