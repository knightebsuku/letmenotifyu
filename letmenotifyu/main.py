#!/usr/bin/python3

import sqlite3
import logging
from datetime import datetime, timedelta
from gi.repository import Gtk, Gdk
from letmenotifyu import gui
from letmenotifyu.torrent import Torrent
from letmenotifyu import util
from letmenotifyu import settings
from letmenotifyu import background_worker as bw

class Main(object):
    "Main application"
    def __init__(self):
        self.connect = sqlite3.connect(settings.DATABASE_PATH)
        self.cursor = self.connect.cursor()
        self.connect.execute("PRAGMA journal_mode=WAL")
	self.connect.execute("PRAGMA foreign_keys = ON")
        self.db_file = settings.DATABASE_PATH
        self.builder = Gtk.Builder()
        self.image = Gtk.Image()
        self.torrent = Torrent(self.cursor)
        self.flag = ""
        self.builder.add_from_file("ui/Main.glade")
        signals = {'on_AppWindow_destroy': Gtk.main_quit,
                   'on_HeaderView_event': self.header_view_event,
                   'on_GeneralIconView_activated': self.general_view_activate,
                   'on_GeneralIconView_event': self.general_view_event,
                   'on_AddSeries_activate': self.add_series_activate,
                   'on_Stop_Update_activate': self.stop_update_activate,
                   'on_Start_Update_activate': self.start_update_activate,
                   'on_Delete_Series_activate': self.delete_series_activate,
                   'on_Current_Season_activate': self.set_season_activate,
                   'on_preferences_activate': self.pref_activate,
                   'on_Quit_activate': self.on_quit,
                   'on_About_activate': self.about_activate,
                   'on_Kickass_activate': self.kickass_activate,
                   'on_BtnRoot_clicked': self.button_root_clicked,
                   'on_BtnLevel1_clicked': self.button_one_clicked,
                   'on_BtnLevel2_clicked': self.button_two_clicked,
                   'on_queue_activate': self.upcoming_queue,
                   'on_search_search_changed': self.search_changed,
                   'on_series_watch_activate': self.series_watch,
                   'on_watchlist_activate': self.watch_list}

        self.builder.connect_signals(signals)
        self.header_dic = {'Released Movies': self.released_movies,
                      'Upcoming Movies': self.upcoming_movies,
                      'Latest Episodes': self.latest_episodes,
                      'Active Series': self.active_series,
                      'Series Archive': self.series_archive,
                      'Movie Queue': self.watch_movies,
                      'Series Queue': self.watch_series}
        self.general_model = self.builder.get_object("General")
        self.general_icon_view = self.builder.get_object('GeneralIconView')
        self.button_level_1 = self.builder.get_object("BtnLevel1")
        self.button_level_2 = self.builder.get_object("BtnLevel2")
        util.pre_populate_menu(self.builder)
        self.builder.get_object('AppWindow').show()
        bw.start_threads()
        Gtk.main()

    def on_quit(self, widget):
        self.cursor.execute("PRAGMA wal_checkpoint(PASSIVE)")
        Gtk.main_quit()

    def general_view_activate(self, widget, choice):
        if self.flag == "upcoming movies":
            util.open_page(self.cursor, choice, "upcoming")
        elif self.flag == "latest episodes":
            util.open_page(self.cursor, self.latest_dict[choice])
        elif self.flag == "released movies":
            self.released_movies_select(choice)
            self.button_level_1.set_property("visible", True)
            self.button_level_1.set_property("label", choice)
        elif self.flag == "genre select":
            gui.MovieDetails(self.cursor, self.connect, choice)
        elif self.flag == "active series":
            self.active_series_select(choice)
            self.button_level_1.set_property("visible", True)
            self.button_level_1.set_property("label", choice)
        elif self.flag == "select series":
            util.open_page(self.cursor, self.active_series_dic[choice])
        elif self.flag == "series archive":
            self.series_archive_select(choice)
            self.button_level_1.set_property("visible", True)
            self.button_level_1.set_property("label", choice)
        elif self.flag == "no seasons":
            self.season_select(choice)
            self.button_level_2.set_property("visible", True)
            self.button_level_2.set_property("label", choice)
        elif self.flag == "season select":
            util.open_page(self.cursor, self.archive_series_dict[choice])
        
    def general_view_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            path = widget.get_path_at_pos(event.x, event.y)
            if path:
                widget.select_path(path)
                self.choice = util.get_selection(widget, self.general_model)
                self.striped_name = self.choice.split(" Season")[0]
                if event.button == 1:
                    self.general_view_activate(widget, self.choice)
                elif event.button == 3 and self.flag == "series archive":
                    self.builder.get_object("Series").popup(None, None, None, None,
                                                            event.button, event.time)
                elif event.button == 3 and self.flag == "active series":
                    self.builder.get_object("Series").popup(None, None, None, None,
                                                            event.button, event.time)
                elif event.button == 3 and self.flag == "latest episodes":
                    self.torrent.query(self.choice)
                    self.builder.get_object("torrents").popup(None, None, None, None,
                                                       event.button, event.time)
                elif event.button == 3 and self.flag == "upcoming movies":
                    self.builder.get_object("upcoming").popup(None, None, None, None,
                                                              event.button, event.time)
                elif event.button == 3 and self.flag == "watch series":
                    self.builder.get_object("RemoveQueue").popup(None, None, None, None,
                                                                 event.button, event.time)

    def header_view_event(self, widget, event):
        button_root = self.builder.get_object("BtnRoot")
        if event.button == 1:
            selection = widget.get_selection()
            name, itr = selection.get_selected()
            header_choice = name[itr][0]
            try:
                self.header_dic[header_choice]()
                button_root.set_property("label", header_choice)
                button_root.set_property("visible", True)
                self.button_level_1.set_property("visible", False)
                self.button_level_2.set_property("visible", False)
            except KeyError:
                pass

    def released_movies_select(self,choice):
        self.cursor.execute("SELECT id from genre where genre=?",
                                (choice,))
        self.search_choice = choice
        (genre_key,) = self.cursor.fetchone()
        self.cursor.execute("SELECT movies.title,path from movies,movie_images " +
                                "WHERE movies.title=movie_images.title "+
                                "and  movies.genre_id=? order by movies.title",
                                (genre_key,))
        movie_info = self.cursor.fetchall()
        self.general_model.clear()
        for (movie_title, path) in movie_info:
            util.render_view(self.image, movie_title,
                                 self.general_model, settings.IMAGE_PATH+path)
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
        for (episode_name, episode_link) in self.cursor.fetchall():
            util.render_view(self.image, episode_name, self.general_model)
            self.active_series_dic[episode_name] = episode_link
        self.flag = "select series"
        

    def released_movies(self):
        self.general_model.clear()
        self.cursor.execute("SELECT genre from genre order by genre")
        result = self.cursor.fetchall()
        for genre in result:
            self.image.set_from_file("icons/"+genre[0]+'.png')
            pixbuf = self.image.get_pixbuf()
            self.general_model.append([pixbuf, genre[0]])
        self.flag = "released movies"

    def upcoming_movies(self):
        self.general_model.clear()
        self.cursor.execute("SELECT upcoming_movies.title,path from upcoming_movies"+
                            ",movie_images "+
                            "where upcoming_movies.title=movie_images.title ORDER BY upcoming_movies.id DESC")
        movies = self.cursor.fetchall()
        for movie in movies:
            util.render_view(self.image, movie[0], self.general_model,
                             settings.IMAGE_PATH+movie[1])
        self.flag = "upcoming movies"

    def latest_episodes(self):
        self.latest_dict = {}
        self.general_model.clear()
        self.cursor.execute("SELECT value from config where key='series_duration'")
        duration = self.cursor.fetchone()
        week = datetime.now() - timedelta(days=float(duration[0]))
        self.cursor.execute("SELECT episode_name,episode_link,path from episodes "+
                            "join series_images "+
                            "on episodes.series_id=series_images.series_id "+
                            "and episodes.Date BETWEEN ? AND ?",
                            (week, datetime.now(),))
        for (episode_name, episode_link, path) in self.cursor.fetchall():
            util.render_view(self.image, episode_name, self.general_model,
                             settings.IMAGE_PATH+path)
            self.latest_dict[episode_name] = episode_link
        self.flag = 'latest episodes'

    def active_series(self):
        self.general_model.clear()
        self.cursor.execute("SELECT title,current_season,path  from series "+
                            "join series_images on series.id=series_images.series_id and "+
                            "series.status=1 order by title")
        for (title, current_season, path) in self.cursor.fetchall():
            util.render_view(self.image, title+" "+"Season"+" "+str(current_season),
                              self.general_model, settings.IMAGE_PATH+path)
        self.flag = 'active series'

    def series_archive(self):
        self.general_model.clear()
        self.cursor.execute("SELECT title,path  from series join "+
                            "series_images on series.id=series_images.series_id order by title")
        for (title, path) in self.cursor.fetchall():
            util.render_view(self.image, title, self.general_model,
                                 settings.IMAGE_PATH+path)
            self.flag = 'series archive'

    def series_archive_select(self,choice):
        self.series_name = choice
        self.cursor.execute("SELECT number_of_seasons from series where title=?",
                            (choice,))
        (no_seasons,) = self.cursor.fetchone()
        self.general_model.clear()
        index = 1
        while index <= int(no_seasons):
            util.render_view(self.image, "Season {}".format(index), self.general_model)
            index += 1
        self.flag = "no seasons"
            
    def season_select(self,choice):
        self.archive_series_dict = {}
        no = choice.split("Season ")[1]
        self.cursor.execute("SELECT episode_name,episode_link FROM episodes" +
                            ' WHERE series_id=(SELECT id from series where title=?)' +
                            ' and episode_link LIKE ?',
                            (self.series_name, "%season-" + no + "%",))
        self.general_model.clear()
        for (episode_name,episode_link) in self.cursor.fetchall():
            util.render_view(self.image, episode_name, self.general_model)
            self.archive_series_dict[episode_name] = episode_link
        self.flag = "season select"

    def watch_movies(self):
        self.general_model.clear()
        self.cursor.execute("select mi.path,wqs.name from "+
                            'movie_images as mi,'+
                            'watch_queue_status as wqs,'+
                            'movie_queue as mq '+
                            'where mi.title=(select title from movies where id=mq.movie_id) '+
                            'and wqs.id=mq.watch_queue_status_id')
        for (path, watch_name) in self.cursor.fetchall():
            util.render_view(self.image, watch_name, self.general_model,
                             settings.IMAGE_PATH+path)
        self.flag = 'watch movies'

    def watch_series(self):
        self.general_model.clear()
        self.cursor.execute("select si.path,wqs.name,sq.episode_name from "+
                            'series_images as si,'+
                            'watch_queue_status as wqs,'+
                             'series_queue as sq '+
                             'where wqs.id=sq.watch_queue_status_id '+
                             'and sq.series_id=si.series_id')
        for (path, watch_name, episode_name) in self.cursor.fetchall():
            util.render_view(self.image, episode_name+":  "+watch_name, self.general_model,
                             settings.IMAGE_PATH+path)
        self.flag = 'watch series'
        
    def button_root_clicked(self, widget):
        self.header_dic[widget.get_label()]()

    def button_one_clicked(self, widget):
        if self.flag in ("released movies", "genre select"):
            self.released_movies_select(widget.get_label())
        elif self.flag in ("active series", "select series"):
            self.active_series_select(widget.get_label())
        elif self.flag in ("season select", "series_archive"):
            self.series_archive_select(widget.get_label())

    def button_two_clicked(self, widget):
        self.season_select(widget.get_label())

    def add_series_activate(self, widget):
        gui.AddSeries(self.cursor, self.connect)

    def about_activate(self, widget):
        gui.About()

    def kickass_activate(self, widget):
        self.torrent.kickass()

    def stop_update_activate(self, widget):
        gui.Confirm(self.striped_name, "stop", self.connect, self.cursor)

    def start_update_activate(self, widget):
        gui.Confirm(self.striped_name, "start", self.connect, self.cursor)

    def delete_series_activate(self, widget):
        gui.Confirm(self.striped_name, "delete", self.connect, self.cursor)

    def pref_activate(self, widget):
        gui.Preferences(self.cursor, self.connect)

    def set_season_activate(self, widget):
        gui.SetSeason(self.cursor, self.connect, self.striped_name)

    def upcoming_queue(self, widget):
        try:
            self.cursor.execute("INSERT INTO upcoming_queue(title) "+
                                "SELECT title from upcoming_movies where title=?",(self.choice,))
            self.connect.commit()
            gui.Error("{} added to upcoming queue".format(self.choice))
        except sqlite3.IntegrityError:
            gui.Error("record is already in upcoming queue")
            logging.warn("record is already in upcoming_queue")

    def search_changed(self, widget):
        "change search only for movies"
        if self.flag == 'upcoming movies':
            self.general_model.clear()
            self.cursor.execute("SELECT upcoming_movies.title,path from upcoming_movies"+
                            ",movie_images "+
                            "where upcoming_movies.title=movie_images.title and upcoming_movies.title like ('%' || ? || '%')",
                                 (widget.get_text(),))
            movies = self.cursor.fetchall()
            for movie in movies:
                util.render_view(self.image, movie[0], self.general_model,
                             settings.IMAGE_PATH+movie[1])
            self.flag = 'upcoming movies'
        elif self.flag == 'genre select':
            self.cursor.execute("SELECT id from genre where genre=?",
                                (self.search_choice,))
            genre_key = self.cursor.fetchone()
            self.cursor.execute("SELECT movies.title,path from movies,movie_images " +
                                "WHERE movies.title=movie_images.title "+
                                "and  movies.genre_id=? and movies.title like ('%' || ? || '%') ",
                                (genre_key[0], widget.get_text(),))
            self.general_model.clear()
            for (title, path) in self.cursor.fetchall():
                util.render_view(self.image, title,
                                 self.general_model, settings.IMAGE_PATH+path)
            self.flag = "genre select"

    def series_watch(self, widget):
        "add series to watch list"
        if self.flag == 'series archive':
            try:
                self.connect.execute("UPDATE series set watch=1 where title=?",(self.choice,))
                self.connect.commit()
                gui.Error("{} has been added to the watch list".format(self.choice))
            except sqlite3.OperationalError as e:
                logging.exception(e)

    def watch_list(self, widget):
        "add movie to watch queue"
        try:
            self.cursor.execute("INSERT INTO movie_queue(movie_id,watch_queue_status_id) "+
                                "SELECT movies.id,watch_queue_status.id FROM movies,watch_queue_status "+
                                "WHERE movies.title=? and watch_queue_status.name='new'",(self.choice,))
            self.connect.commit()
            gui.Error("{} has been added to the watch list".format(self.choice))
        except sqlite3.IntegrityError:
            gui.Error("record is already in the movie queue")
            logging.info("recored is already in movie queue")
