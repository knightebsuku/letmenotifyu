#!/usr/bin/python3

import logging
import configparser
import sqlite3
import re
from datetime import datetime
from gi.repository import Gtk, GObject
from gi.repository.GdkPixbuf import Pixbuf
from letmenotifyu import util
from letmenotifyu import settings
from threading import Thread
from letmenotifyu.movies import get_movie_details


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
    def __init__(self, cursor, connection):
        self.cursor = cursor
        self.connection = connection
        self.dialog = Gtk.Builder()
        self.dialog.add_from_file("ui/AddSeries.glade")
        connectors = {'on_btnCancel_clicked': self.cancel_clicked,
              'on_btnOk_clicked': self.ok_clicked}
        self.dialog.connect_signals(connectors)
        self.notice = self.dialog.get_object('lblNotice')
        self.link_box = self.dialog.get_object('entLink')
        self.dialog.get_object('Dialog').show()

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
                self.dialog.get_object('Dialog').destroy()
            except sqlite3.IntegrityError:
                self.connection.rollback()
                logging.error("Series already added")
                self.notice.set_text("Series already added")
                self.notice.set_visible(True)
                self.dialog.get_object('imCheck').set_visible(True)
        else:
            self.notice.set_text("Not a valid link or link already exists")
            self.notice.set_visible(True)
            self.dialog.get_object('imCheck').set_visible(True)
            logging.warn("Invalid link:"+text)


    def cancel_clicked(self, widget):
        self.dialog.get_object('Dialog').destroy()

    def ok_clicked(self, widget):
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
            use_sql = "UPDATE series SET status=1 where title=?"
            message = "Are you sure you want to start updating"
        elif self.instruction == "stop":
            use_sql = "UPDATE series SET status=0 where title=?"
            message = "Are you sure you want to stop updating"
        elif self.instruction == "delete":
            use_sql = "DELETE FROM series WHERE title=?"
            message = "Are you sure you want to delete"
        return message, use_sql


    def ok_clicked(self, widget):
        "confirm deletion"
        self.cursor.execute(self.sql, (self.title,))
        self.connect.commit()
        self.confirm.get_object('msgDialog').destroy()
        logging.warn("Deleting: "+self.title)

    def cancel_clicked(self, widget):
        self.confirm.get_object('msgdlg').destroy()

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
        "save to file"
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
        
    def save_clicked(self, widget):
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


class SetSeason(object):
    "Current season popup"
    def __init__(self, cursor, connection, series_title):
        self.cursor = cursor
        self.connection = connection
        self.series_title = series_title
        self.current_season = Gtk.Builder()
        self.current_season.add_from_file("ui/SetSeason.glade")
        signals = {'on_btnApply_clicked': self.apply_clicked,
                 'on_btnCancel_clicked': self.cancel_clicked}
        self.current_season.connect_signals(signals)
        cur_sea = self.fetch_current_season(series_title)
        self.current_season.get_object('txtCurrent').set_text(str(cur_sea))
        self.current_season.get_object("CurrentSeason").show()

    def fetch_current_season(self, series_title):
        self.cursor.execute('SELECT current_season from series where title=?', (series_title,))
        (no_season,) = self.cursor.fetchone()
        return no_season

    def cancel_clicked(self, widget):
        self.current_season.get_object('CurrentSeason').close()

    def apply_clicked(self, widget):
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
        signals = {'on_btnFetchDetails_clicked': self.fetch_details,
                   'on_btnWatchList_clicked': self.watch_list,
                   'on_btnClose_clicked': self.close}
        self.details.connect_signals(signals)
        self.populate()
        self.details.get_object("winMovieDetails").show()

    def populate(self):
        movie_image = self.details.get_object("imageMovie")
        movie_title = self.details.get_object("lblMovieTitle")
        rating = self.details.get_object("lblRating")
        movie_link = self.details.get_object("lkImdb")
        youtube_link = self.details.get_object("lkYoutubeUrl")
        self.watch_list = self.details.get_object("lblWatchList")
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
            self.watch_list.set_text("Yes")
            self.details.get_object("btnWatchList").set_sensitive(False)
        else:
            self.watch_list.set_text("No")
        self.cursor.execute("SELECT movie_rating,youtube_url,description from movie_details "+
                            'WHERE movie_id=(SELECT id FROM movies where title=?)',(self.movie_title,))
        if self.cursor.fetchone() is None:
            rating.set_text("")
            youtube_link.set_uri("")
            youtube_link.set_property("visible", False)
            description.set_text("")
            self.details.get_object("lkActor1").set_property("visible", False)
            self.details.get_object("lkActor2").set_property("visible", False)
            self.details.get_object("lkActor3").set_property("visible", False)
            self.details.get_object("lkActor4").set_property("visible", False)
        else:
            self.cursor.execute("SELECT movie_rating,youtube_url,description from movie_details "+
                            'WHERE movie_id=(SELECT id FROM movies where title=?)',(self.movie_title,))
            (r, yu, des,) = self.cursor.fetchone()
            rating.set_text(str(r))
            youtube_link.set_uri(yu)
            youtube_link.set_property('label',"Trailer")
            description.set_text(des)
            self.cursor.execute("SELECT name FROM actors AS a JOIN actors_movies AS am "+
                           'ON a.id=am.actor_id AND am.movie_id='+
                           '(SELECT id FROM movies WHERE title=?)',(self.movie_title,))
            cast_list = {1: self.details.get_object("lblActor1"), 2: self.details.get_object("lblActor2"),
                         3: self.details.get_object("lblActor3"),4: self.details.get_object("lblActor4")}
            key = 1
            for (name,) in self.cursor.fetchall():
                cast_list[key].set_text(name)
                key += 1
            self.details.get_object("btnFetchDetails").set_sensitive(False)
    def fetch_details(self, widget):
        "fetch details if not present"
        self.details.get_object("spFetch").start()
        fetch  = WorkerThread(self.stop_spin, self.movie_title)
        fetch.start()
        
    def watch_list(self, widget):
        "add to watch list"
        self.cursor.execute("INSERT INTO movie_queue(movie_id,watch_queue_status_id) "+
                                "SELECT movies.id,watch_queue_status.id FROM movies,watch_queue_status "+
                                "WHERE movies.title=? and watch_queue_status.name='new'",(self.movie_title,))
        self.connect.commit()
        self.watch_list.set_text("Yes")
        self.details.get_object("btnWatchList").set_sensitive(False)
    def close(self, widget):
        "close widget"
        self.details.get_object("winMovieDetails").destroy()

    def stop_spin(self,status):
        if status == 'no fetch':
            Error("Unable to fetch movie details")
        elif status == "no detail":
            Error("No movie details at this moment")
        else:
            self.populate()
        self.details.get_object("spFetch").stop()
        

def details(movie_title):
    "fetching details"
    connect = sqlite3.connect(settings.DATABASE_PATH)
    cursor = connect.cursor()
    cursor.execute("SELECT id,movie_id from movies where title=?",(movie_title,))
    (movie_id, yify_id,) = cursor.fetchone()
    movie_detail = get_movie_details(yify_id)
    if not movie_detail:
        logging.error("Unable to fetch movie details")
        status = "no fetch"
    elif 'status' in movie_detail.keys():
        logging.error("No movie details at this time")
        status = "no detail"
    else:
        try:
            connect.execute("INSERT INTO movie_details(movie_id,language,movie_rating,"+
                                    'youtube_url,description) '+
                                    'VALUES(?,?,?,?,?)',(movie_id,movie_detail['Language'],
                                                         movie_detail['MovieRating'],
                                                         movie_detail["YoutubeTrailerUrl"],
                                                         movie_detail["LongDescription"],))
            for actor in movie_detail["CastList"]:
                try:
                    row = connect.execute("INSERT INTO actors(name,actor_link) "+
                                          'VALUES(?,?)',(actor["ActorName"], actor['ActorImdbLink'],))
                    connect.execute("INSERT INTO actors_movies(actor_id,movie_id) "+
                                    'VALUES(?,?)',(row.lastrowid, movie_id,))
                    connect.commit()
                    status =  "ok"
                except sqlite3.IntegrityError:
                    logging.error("Actor already exists")
                    cursor.execute("SELECT id from actors where name=?", (actor["ActorName"],))
                    (actor_id,) = cursor.fetchone()
                    connect.execute("INSERT INTO actors_movies(actor_id,movie_id) "+
                                        'VALUES(?,?)', (actor_id,movie_id,))
                    logging.info("Movie Detail complete")
                    status = "ok"
                except sqlite3.OperationalError as e:
                    logging.exception(e)
                    status = "no detail"
                finally:
                    connect.commit()
        except sqlite3.OperationalError as e:
            logging.exception(e)
            return "no detail"
            
    connect.close()
    return status
             
class WorkerThread(Thread):
    def __init__(self,callback,movie_title):
        Thread.__init__(self)
        self.callback = callback
        self.movie_title = movie_title

    def run(self):
        status = details(self.movie_title)
        GObject.idle_add(self.callback, status)
