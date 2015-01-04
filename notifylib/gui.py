import logging
from gi.repository import Gtk
from notifylib import util

class About(object):
    "Show about menu"
    def __init__(self):
        about = Gtk.Builder()
        about.add_from_file("ui/about.glade")
        window = about.get_object('abtdlg')
        window.run()
        window.destroy()


class Add_Series(object):
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
        self.dialog.get_object('linkdialog').show()

    def on_btnCancel_clicked(self, widget):
        self.dialog.get_object('linkdialog').destroy()

    def on_btnOk_clicked(self, widget):
        link_box = self.dialog.get_object('entlink')
        util.check_url(link_box.get_text(), self.notice, self.dialog,
                  self.cursor, self.connection, link_box)
        link_box.set_text('')


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
        self.message, self.sql = util.which_sql_message(self.instruction)
        self.confirm.get_object('msgdlg').format_secondary_text(self.message+" " +
                                                                self.title+"?")
        self.confirm.get_object('msgdlg').show()

    def on_btnOk_clicked(self, widget):
        self.cursor.execute(self.sql, (self.title,))
        self.connect.commit()
        self.confirm.get_object('msgdlg').destroy()
        logging.warn("Deleting: "+self.title)

    def on_btnCancel_clicked(self, widget):
        self.confirm.get_object('msgdlg').destroy()


class Statistics(object):
    "Show stats of series"
    def __init__(self, title, connect, cursor):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/stats.glade")
        signals = {'on_btnClose_clicked': self.on_btnClose_clicked}
        self.builder.connect_signals(signals)
        util.set_stats(title, connect, cursor, self.builder)
        self.builder.get_object('win_stats').show()

    def on_btnClose_clicked(self, widget):
        self.builder.get_object("win_stats").destroy()

class Preferences(object):
    "preference menu"
    def __init__(self, cursor, connect):
        self.cursor = cursor
        self.connect = connect
        self.pref = Gtk.Builder()
        self.pref.add_from_file("ui/preferences.glade")
        signals = {'on_btnSave_clicked': self.on_btnSave_clicked,
                 'on_btnCancel_clicked': self.on_btnCancel_clicked}
        self.pref.connect_signals(signals)
        self.interval = self.pref.get_object('txtupdate')
        self.movie_update = self.pref.get_object('txtmovies')
        self.series_update = self.pref.get_object('txtseries')
        util.get_intervals(self.cursor, self.interval, self.movie_update, self.series_update)
        self.pref.get_object('pref').show()

    def on_btnSave_clicked(self, widget):
        try:
            update  = str(float(self.interval.get_text())*3600)
            series_duration = str(int(self.series_update.get_text()))
            movie_duration = str(int(self.movie_update.get_text()))
            self.cursor.execute("UPDATE config set value=? where key='update_interval'",
                                (update,))
            self.cursor.execute("UPDATE config set value=? where key='series_duration'",
                                (series_duration,))
            self.cursor.execute("UPDATE config set value=? where key='movie_duration'",
                                (movie_duration,))
            self.connect.commit()
            self.pref.get_object('pref').destroy()

        except ValueError as e:
            logging.info("Not a valid number")
            logging.exception(e)
            self.connect.rollback()
            Error("Not a valid number")

    def on_btnCancel_clicked(self, widget):
        self.pref.get_object('pref').destroy()


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
        cur_sea = util.fetch_current_season(cursor, connection, series_title)
        self.current_season.get_object('txtCurrent').set_text(cur_sea)
        self.current_season.get_object("CurrentSeason").show()

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
