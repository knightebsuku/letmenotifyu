#!/usr/bin/python3

import logging
import configparser
import sqlite3
import re
from datetime import datetime
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf
from letmenotifyu import util
from letmenotifyu import settings

class About(object):
    "Show about menu"
    def __init__(self):
        about = Gtk.Builder()
        about.add_from_file("ui/about.glade")
        window = about.get_object('AboutDialog')
        window.run()
        window.destroy()


class AddSeries(object):
    "Addition of new series"
    def __init__(self, cursor, connection):
        self.cursor = cursor
        self.connection = connection
        self.dialog = Gtk.Builder()
        self.dialog.add_from_file("ui/add_series.glade")
        connectors = {'on_btnCancel_clicked': self.on_btnCancel_clicked,
              'on_btnOk_clicked': self.on_btnOk_clicked}
        self.dialog.connect_signals(connectors)
        self.notice = self.dialog.get_object('lblNotice')
        self.link_box = self.dialog.get_object('entlink')
        self.dialog.get_object('linkdialog').show()

    def check_url(self,text):
        "check adding new series"
        if re.search(r'http://www.primewire.ag/(.*)-\d+-(.*)-online-free', text):
            title = re.search(r"http://www.primewire.ag/(.*)-\d+-(.*)-online-free", text)
            change_string = title.group(2)
            show_title = change_string.replace("-", " ")
            logging.info("Inserting new series {}".format(show_title))
            try:
                self.cursor.execute('INSERT INTO series(title,' +
                               'series_link,' +
                               'number_of_episodes,' +
                               'number_of_seasons,' +
                               'status,' +
                               'current_season,' +
                               'last_update)' +
                               ' VALUES(?,?,0,0,1,0,?)',
                               (show_title, text, datetime.now(),))
                self.connection.commit()
                logging.debug("Series Added: {}".format(show_title))
                self.link_box.set_text('')
                self.dialog.get_object('linkdialog').destroy()
            except sqlite3.IntegrityError:
                self.connection.rollback()
                logging.error("Series already added")
                self.notice.set_text("Series already added")
                self.notice.set_visible(True)
                self.dialog.get_object('imcheck').set_visible(True)
        else:
            self.notice.set_text("Not a valid link or link already exists")
            self.notice.set_visible(True)
            self.dialog.get_object('imcheck').set_visible(True)
            logging.warn("Invalid link:"+text)


    def on_btnCancel_clicked(self, widget):
        self.dialog.get_object('linkdialog').destroy()

    def on_btnOk_clicked(self, widget):
        self.check_url(self.link_box.get_text())
        self.link_box.set_text('')


class Confirm(object):
    "Confirm menu"
    def __init__(self,title, instruction, connect, cursor):
        self.connect = connect
        self.cursor = cursor
        self.title = title
        self.instruction = instruction
        self.confirm = Gtk.Builder()
        self.confirm.add_from_file("ui/confirm.glade")
        signals = {'on_btnOk_clicked': self.on_btnOk_clicked,
               'on_btnCancel_clicked': self.on_btnCancel_clicked}
        self.confirm.connect_signals(signals)
        self.message, self.sql = self.which_sql_message()
        self.confirm.get_object('msgdlg').format_secondary_text(self.message+" " +
                                                                self.title+"?")
        self.confirm.get_object('msgdlg').show()

    def which_sql_message(self):
        if self.instruction == "start":
            use_sql = "UPDATE series SET status=1 where title=?"
            message = "Are you sure you want to start updating"
        elif self.instruction == "stop":
            use_sql = "UPDATE series SET status=0 where title=?"
            message = "Are you sure you want to stop updating"
        elif self.instruction == "delete":
            use_sql = "DELETE FROM series WHERE title=?"
            message = "Are you sure you want to delete"
        return message, use_sql


    def on_btnOk_clicked(self, widget):
        self.cursor.execute(self.sql, (self.title,))
        self.connect.commit()
        self.confirm.get_object('msgdlg').destroy()
        logging.warn("Deleting: "+self.title)

    def on_btnCancel_clicked(self, widget):
        self.confirm.get_object('msgdlg').destroy()

class Preferences(object):
    "preference menu"
    def __init__(self, cursor, connect):
        self.cursor = cursor
        self.connect = connect
        self.pref = Gtk.Builder()
        self.pref.add_from_file("ui/preferences.glade")
        signals = {'on_BtnOK_clicked': self.on_btnSave_clicked,
                 'on_BtnCancel_clicked': self.on_btnCancel_clicked}
        self.pref.connect_signals(signals)
        self.populate_fields()
        self.pref.get_object('Preference').show()

    def populate_fields(self):
        update_interval  = util.get_config_value(self.cursor,"update_interval")
        movie_process = util.get_config_value(self.cursor,"movie_process_interval")
        series_process = util.get_config_value(self.cursor,"series_process_interval")
        series_duration = util.get_config_value(self.cursor,"series_duration")
        max_movie_result = util.get_config_value(self.cursor,'max_movie_results')
        self.pref.get_object("spUpdate").set_value(float(update_interval))
        self.pref.get_object("spMovieQueue").set_value(float(movie_process))
        self.pref.get_object("spSeriesQueue").set_value(float(series_process))
        self.pref.get_object("spSeriesDuration").set_value(float(series_duration))
        self.pref.get_object("spMovieResults").set_value(float(max_movie_result))
        self.pref.get_object("fcbImages").set_current_folder(settings.IMAGE_PATH)
        self.pref.get_object("fcbTorrents").set_current_folder(settings.TORRENT_DIRECTORY)
        self.pref.get_object("fcbComplete").set_current_folder(settings.COMPLETE_DIRECTORY)
        self.pref.get_object("fcbIncomplete").set_current_folder(settings.INCOMPLETE_DIRECTORY)

    def write_to_config(self):
        config = configparser.ConfigParser()
        images = self.pref.get_object("fcbImages").get_current_folder()
        torrents = self.pref.get_object("fcbTorrents").get_current_folder()
        complete = self.pref.get_object("fcbComplete").get_current_folder()
        incomplete = self.pref.get_object("fcbIncomplete").get_current_folder()
        config['DIRECTORIES'] = {'ImagesDIrectory': images+'/',
                             'TorrentsDirectory': torrents+'/',
                             'CompleteDownloads': complete+'/',
                                 'IncompleteDownloads': incomplete+'/'}
        with open(settings.DIRECTORY_PATH+'/config.ini','w') as cfg_file:
            config.write(cfg_file)
        
    def on_btnSave_clicked(self, widget):
        try:
            update_interval = self.pref.get_object("spUpdate").get_value()
            movie_process = self.pref.get_object('spMovieQueue').get_value()
            series_process = self.pref.get_object("spSeriesQueue").get_value()
            movie_results = self.pref.get_object("spMovieResults").get_value()
            series_duration = self.pref.get_object("spSeriesDuration").get_value()
            quality_iter = self.pref.get_object('cbMovieQuality').get_active_iter()
            movie_quality = self.pref.get_object('lsMovieCombo').get_value(quality_iter,0)
            query = [(update_interval, 'update_interval'),
                     (movie_process, 'movie_process_interval'),
                     (series_process, 'series_process_interval'),
                     (movie_results, 'max_movie_results'),
                     (movie_quality, 'movie_quality'),
                     (series_duration, 'series_duration')]
            self.cursor.executemany("UPDATE config set value=? where key=?", query)
            self.connect.commit()
            self.write_to_config()
            self.pref.get_object('Preference').destroy()

        except ValueError as e:
            logging.info("Not a valid number")
            logging.exception(e)
            self.connect.rollback()
            Error("Not a valid number")

    def on_btnCancel_clicked(self, widget):
        self.pref.get_object('Preference').destroy()


class Error(object):
    "Error notification"
    def __init__(self, text):
        self.error = Gtk.Builder()
        self.error.add_from_file("ui/error.glade")
        signals = {'on_btnOk_clicked': self.on_btnOk_clicked}
        self.error.connect_signals(signals)
        self.error.get_object('error').set_property('text', text)
        self.error.get_object('error').show()

    def on_btnOk_clicked(self, widget):
        self.error.get_object('error').destroy()


class Current_Season(object):
    "Current season popup"
    def __init__(self, cursor, connection, series_title):
        self.cursor = cursor
        self.connection = connection
        self.series_title = series_title
        self.current_season = Gtk.Builder()
        self.current_season.add_from_file("ui/set_season.glade")
        signals = {'on_btnApply_clicked': self.on_btnApply_clicked,
                 'on_btnCancel_clicked': self.on_btnCancel_clicked}
        self.current_season.connect_signals(signals)
        cur_sea = self.fetch_current_season(series_title)
        self.current_season.get_object('txtCurrent').set_text(cur_sea)
        self.current_season.get_object("CurrentSeason").show()

    def fetch_current_season(self, series_title):
        self.cursor.execute('SELECT current_season from series where title=?', (series_title,))
        (no_season,) = self.cursor.fetchone()
        return no_season

    def on_btnCancel_clicked(self, widget):
        self.current_season.get_object('CurrentSeason').close()

    def on_btnApply_clicked(self, widget):
        try:
            cur_season = self.current_season.get_object('txtCurrent').get_text()
            self.cursor.execute('UPDATE series set current_season = ? where title=?',
                           (cur_season, self.series_title,))
            self.connection.commit()
            self.current_season.get_object("CurrentSeason").destroy()
        except Exception as e:
            logging.warn("Unable to set current season")
            logging.exception(e)

class MovieDetails(object):
    "show movie details"
    def __init__(self,cursor,connect,movie_title):
        self.cursor = cursor
        self.connect = connect
        self.movie_title = movie_title
        self.details = Gtk.Builder()
        self.details.add_from_file("ui/MovieDetails.glade")
        self.fetch_details()
        self.details.get_object("winMovieDetails").show()

    def fetch_details(self):
        movie_image = self.details.get_object("imageMovie")
        movie_title = self.details.get_object("lblMovieTitle")
        rating = self.details.get_object("lblRating")
        movie_link = self.details.get_object("lkImdb")
        youtube_link = self.details.get_object("lkYoutubeUrl")
        watch_list = self.details.get_object("lblWatchList")
        description = self.details.get_object("bufDescription")
        self.cursor.execute("SELECT movies.title,movies.link,movie_images.path "+
                            'FROM movies,movie_images where movies.title=? '+
                            'AND movie_images.title=?',(self.movie_title,self.movie_title,))
        (mt, ml, mi,)= self.cursor.fetchone()
        movie_title.set_text(mt)
        movie_link.set_uri(ml)
        movie_link.set_property('label',"Imdb")
        pb = Pixbuf.new_from_file(settings.IMAGE_PATH+mi)
        movie_image.set_from_pixbuf(pb)
        self.cursor.execute("SELECT id from movie_queue where movie_id="+
                            '(SELECT id from movies where title=?)',(self.movie_title,))
        if self.cursor.fetchone():
            watch_list.set_text("Yes")
            self.details.get_object("btnWatchList").set_sensitive(False)
        else:
            watch_list.set_text("No")
        self.cursor.execute("SELECT movie_rating,youtube_url,description from movie_details "+
                            'WHERE movie_id=(SELECT id FROM movies where title=?)',(self.movie_title,))
        if self.cursor.fetchone() is None:
            rating.set_text("")
            youtube_link.set_uri("")
            youtube_link.set_property("visible", False)
            description.set_text("")
        else:
            self.cursor.execute("SELECT movie_rating,youtube_url,description from movie_details "+
                            'WHERE movie_id=(SELECT id FROM movies where title=?)',(self.movie_title,))
            (r, yu, des,) = self.cursor.fetchone()
            rating.set_text(str(r))
            youtube_link.set_uri(yu)
            youtube_link.set_property('label',"Trailer")
            description.set_text(des)
            self.details.get_object("btnFetchDetails").set_sensitive(False)
