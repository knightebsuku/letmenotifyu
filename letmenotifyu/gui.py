#!/usr/bin/python3

import logging
import configparser
import psycopg2
import re
import os
import sqlite3


from datetime import datetime
from gi.repository import Gtk
from . import util, settings


class About(object):
    "Show about menu"
    def __init__(self):
        about = Gtk.Builder()
        about.add_from_file("ui/About.glade")
        window = about.get_object('AboutDialog')
        window.run()
        window.destroy()


class AddSeries(object):
    "Addition of new series"
    def __init__(self):
        self.connect = sqlite3.connect(settings.SERIES_DB)
        self.cursor = self.connect.cursor()
        self.cursor.execute(settings.SQLITE_WAL_MODE)
        self.dialog = Gtk.Builder()
        self.dialog.add_from_file("ui/AddSeries.glade")
        connectors = {'on_btnCancel_clicked': self.cancel_clicked,
              'on_btnOk_clicked': self.ok_clicked}
        self.dialog.connect_signals(connectors)
        self.notice = self.dialog.get_object('lblNotice')
        self.link_box = self.dialog.get_object('entLink')
        self.dialog.get_object('Dialog').show()

    def check_url(self, text):
        "check adding new series"
        if re.search(r'http://www.primewire.ag/(.*)-\d+-(.*)-online-free', text):
            title = re.search(r"http://www.primewire.ag/(.*)-\d+-(.*)-online-free", text)
            change_string = title.group(2)
            show_title = change_string.replace("-", " ")
            logging.info("Inserting new series {}".format(show_title))
            try:
                self.cursor.execute('INSERT INTO series(title,'
                                    'series_link,'
                                    'number_of_episodes,'
                                    'number_of_seasons,'
                                    'current_season,'
                                    'last_update)'
                                    " VALUES(?,?,0,0,0,?)",
                                    (show_title, text, datetime.now(),))
                self.connect.commit()
                logging.info("Series Added: {}".format(show_title))
                self.link_box.set_text('')
                self.dialog.get_object('Dialog').destroy()
            except sqlite3.IntegrityError:
                self.connect.rollback()
                logging.error("Series {} already exists".format(show_title))
                self.notice.set_text("Series already added")
                self.notice.set_visible(True)
                self.dialog.get_object('imCheck').set_visible(True)
            finally:
                self.connect.close()
        else:
            self.notice.set_text("Not a valid link or link already exists")
            self.notice.set_visible(True)
            self.dialog.get_object('imCheck').set_visible(True)
            logging.error("Invalid link: {}".format(text))

    def cancel_clicked(self, widget):
        self.dialog.get_object('Dialog').destroy()

    def ok_clicked(self, widget):
        self.check_url(self.link_box.get_text())
        self.link_box.set_text('')


class Confirm(object):
    "Confirm menu"
    def __init__(self, title, instruction, connect, cursor):
        self.connect = connect
        self.cursor = cursor
        self.title = title
        self.instruction = instruction
        self.confirm = Gtk.Builder()
        self.confirm.add_from_file("ui/Confirm.glade")
        signals = {'on_btnOk_clicked': self.ok_clicked,
               'on_btnCancel_clicked': self.cancel_clicked}
        self.confirm.connect_signals(signals)
        self.message, self.sql = self.which_sql_message()
        self.confirm.get_object('msgDialog').format_secondary_text(self.message+" " +
                                                                self.title+"?")
        self.confirm.get_object('msgDialog').show()

    def which_sql_message(self):
        if self.instruction == "start":
            use_sql = "UPDATE series SET status='1' WHERE title=%s"
            message = "Are you sure you want to start updating"
        elif self.instruction == "stop":
            use_sql = "UPDATE series SET status='0' WHERE title=%s"
            message = "Are you sure you want to stop updating"
        elif self.instruction == "delete":
            use_sql = "DELETE FROM series WHERE title=%s"
            message = "Are you sure you want to delete"
        return message, use_sql

    def ok_clicked(self, widget):
        "confirm deletion"
        self.cursor.execute(self.sql, (self.title,))
        self.connect.commit()
        self.confirm.get_object('msgDialog').destroy()
        logging.warn("Deleting: {}".format(self.title))

    def cancel_clicked(self, widget):
        self.confirm.get_object('msgDialog').destroy()


class Preferences(object):
    "preference menu"
    def __init__(self, cursor, connect):
        self.cursor = cursor
        self.connect = connect
        self.pref = Gtk.Builder()
        self.pref.add_from_file("ui/Preferences.glade")
        signals = {'on_btnOK_clicked': self.save_clicked,
                 'on_btnCancel_clicked': self.cancel_clicked}
        self.pref.connect_signals(signals)
        self.populate_fields()
        self.pref.get_object('Preference').show()

    def populate_fields(self):
        "populate fields"
        update_interval = util.get_config_value(self.cursor, "update_interval")
        movie_process = util.get_config_value(self.cursor, "movie_process_interval")
        series_process = util.get_config_value(self.cursor, "series_process_interval")
        series_duration = util.get_config_value(self.cursor, "series_duration")
        max_movie_result = util.get_config_value(self.cursor, 'max_movie_results')
        transmission_host = util.get_config_value(self.cursor, 'transmission_host')
        transmission_port = util.get_config_value(self.cursor, 'transmission_port')
        self.pref.get_object("spUpdate").set_value(float(update_interval))
        self.pref.get_object("spMovieQueue").set_value(float(movie_process))
        self.pref.get_object("spSeriesQueue").set_value(float(series_process))
        self.pref.get_object("spSeriesDuration").set_value(float(series_duration))
        self.pref.get_object("spMovieResults").set_value(float(max_movie_result))
        self.pref.get_object("fcbImages").set_current_folder(settings.IMAGE_PATH)
        self.pref.get_object("fcbTorrents").set_current_folder(settings.TORRENT_DIRECTORY)
        self.pref.get_object("fcbComplete").set_current_folder(settings.COMPLETE_DIRECTORY)
        self.pref.get_object("fcbIncomplete").set_current_folder(settings.INCOMPLETE_DIRECTORY)
        self.pref.get_object("entHost").set_text(transmission_host)
        self.pref.get_object("spPort").set_value(float(transmission_port))

    def write_to_config(self):
        "save to configurations to file"
        config = configparser.ConfigParser()
        images = self.pref.get_object("fcbImages").get_current_folder()
        torrents = self.pref.get_object("fcbTorrents").get_current_folder()
        complete = self.pref.get_object("fcbComplete").get_current_folder()
        incomplete = self.pref.get_object("fcbIncomplete").get_current_folder()
        config['DIRECTORIES'] = {'ImagesDIrectory': images+os.sep,
                             'TorrentsDirectory': torrents+os.sep,
                             'CompleteDownloads': complete+os.sep,
                                 'IncompleteDownloads': incomplete+os.sep
        }
        config["LOGGING"] = {'LoggingLevel': "Logging.INFO"}
        config['DATABASE'] = {'Host': settings.DB_HOST,
                          'Port': settings.DB_PORT,
                          'User': settings.DB_USER,
                          'Password': settings.DB_PASSWORD,
                          'Database': settings.DB_NAME}
        with open(settings.DIRECTORY_PATH+'/config.ini','w') as cfg_file:
            config.write(cfg_file)

    def save_clicked(self, widget):
        try:
            update_interval = self.pref.get_object("spUpdate").get_value()
            movie_process = self.pref.get_object('spMovieQueue').get_value()
            series_process = self.pref.get_object("spSeriesQueue").get_value()
            movie_results = self.pref.get_object("spMovieResults").get_value()
            series_duration = self.pref.get_object("spSeriesDuration").get_value()
            quality_iter = self.pref.get_object('cbMovieQuality').get_active_iter()
            movie_quality = self.pref.get_object('lsMovieCombo').get_value(quality_iter, 0)
            trans_host = self.pref.get_object('entHost').get_text()
            trans_port = self.pref.get_object('spPort').get_value()
            query = [(update_interval, 'update_interval'),
                     (movie_process, 'movie_process_interval'),
                     (series_process, 'series_process_interval'),
                     (movie_results, 'max_movie_results'),
                     (movie_quality, 'movie_quality'),
                     (series_duration, 'series_duration'),
                     (trans_host, 'transmission_port'),
                     (trans_port, 'transmission_port')]
            self.cursor.executemany("UPDATE config SET value=%s WHERE key=%s", query)
            self.connect.commit()
            self.write_to_config()
            self.pref.get_object('Preference').destroy()

        except ValueError as e:
            logging.info("Not a valid number")
            logging.exception(e)
            self.connect.rollback()
            Error("Not a valid number")

    def cancel_clicked(self, widget):
        self.pref.get_object('Preference').destroy()


class Error(object):
    "Error notification"
    def __init__(self, text):
        self.error = Gtk.Builder()
        self.error.add_from_file("ui/Error.glade")
        signals = {'on_btnOk_clicked': self.on_btnOk_clicked}
        self.error.connect_signals(signals)
        self.error.get_object('msgError').set_property('text', text)
        self.error.get_object('msgError').show()

    def on_btnOk_clicked(self, widget):
        self.error.get_object('msgError').destroy()


class MovieDetails(object):
    "show movie details"
    def __init__(self, cursor, connect, movie_title):
        self.cursor = cursor
        self.connect = connect
        self.movie_title = movie_title
        self.details = Gtk.Builder()
        self.details.add_from_file("ui/MovieDetails.glade")
        signals = {'on_btnWatchList_clicked': self.watch_list,
                   'on_btnClose_clicked': self.close}
        self.details.connect_signals(signals)
        self.populate()
        self.details.get_object("winMovieDetails").show()

    def populate(self):
        movie_title = self.details.get_object("lblMovieTitle")
        rating = self.details.get_object("lblRating")
        movie_link = self.details.get_object("lkImdb")
        youtube_link = self.details.get_object("lkYoutubeUrl")
        self.watch_list = self.details.get_object("lblWatchList")
        description = self.details.get_object("bufDescription")
        print(self.movie_title)
        self.cursor.execute("SELECT title,link FROM movies "
                            "WHERE title=?",
                            (self.movie_title,))
        (mt, ml,) = self.cursor.fetchone()
        movie_title.set_text(mt)
        movie_link.set_uri("http://www.imdb.com/title/{}".format(ml))
        movie_link.set_property('label', "Imdb")
        self.cursor.execute("select mq.id FROM movie_queue mq JOIN "
                            "movies m ON mq.id=m.id "
                            "AND title=?", (self.movie_title,))
        #self.cursor.execute("SELECT id FROM movie_queue WHERE movie_id="
        #                    '(SELECT id FROM movies WHERE title=?)',
        #                    (self.movie_title,))
        if self.cursor.fetchone():
            self.watch_list.set_text("Yes")
            self.details.get_object("btnWatchList").set_sensitive(False)
        else:
            self.watch_list.set_text("No")
        self.cursor.execute("SELECT movie_rating, youtube_url, description "
                            "FROM movie_details md "
                            "JOIN movies m "
                            "ON md.movie_id=m.id "
                            "AND title=?", (self.movie_title,))
        #self.cursor.execute("SELECT movie_rating,youtube_url,description "
        #                    "FROM movie_details "
        #                    'WHERE movie_id=(SELECT id FROM movies WHERE title=%s)',(self.movie_title,))
        if self.cursor.fetchone() is None:
            rating.set_text("")
            youtube_link.set_uri("")
            youtube_link.set_property("visible", False)
            description.set_text("")
            self.details.get_object("lblActor1").set_property("visible", False)
            self.details.get_object("lblActor2").set_property("visible", False)
            self.details.get_object("lblActor3").set_property("visible", False)
            self.details.get_object("lblActor4").set_property("visible", False)
        else:
            self.cursor.execute("SELECT movie_rating, youtube_url, description "
                                "FROM movie_details md "
                                "JOIN movies m "
                                "ON md.movie_id=m.id "
                                "AND title=?", (self.movie_title,))
            (r, yu, des,) = self.cursor.fetchone()
            rating.set_text(str(r))
            youtube_link.set_uri("https://www.youtube.com/watch?v={}".format(yu))
            youtube_link.set_property('label', "Trailer")
            description.set_text(des)

    def watch_list(self, widget):
        "add to watch list"
        self.cursor.execute("INSERT INTO movie_queue("
                            "movie_id,watch_queue_status_id) "
                            "SELECT movies.id,watch_queue_status.id "
                            "FROM movies,watch_queue_status "
                            "WHERE movies.title=? "
                            "AND watch_queue_status.name='new'",
                            (self.movie_title,))
        self.connect.commit()
        self.watch_list.set_text("Yes")
        self.details.get_object("btnWatchList").set_sensitive(False)

    def close(self, widget):
        "close widget"
        self.details.get_object("winMovieDetails").destroy()
