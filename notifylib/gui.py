import re
import logging
from gi.repository import Gtk
from notifylib.check_updates import UpdateClass
from datetime import datetime

class About:
    def __init__(self):
        about = Gtk.Builder()
        about.add_from_file("ui/about.glade")
        window = about.get_object('abtdlg')
        window.run()
        window.destroy()


class Add_Series:
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
        check_url(link_box.get_text(), self.notice, self.dialog,
                  self.cursor, self.connection, link_box)
        link_box.set_text('')


def check_url(text, notice, dialog, cursor, connection, link_box):
    if re.search(r'http://www.primewire.ag/(.*)-\d+\-(.*)',text):
        title = re.search(r"http://www.primewire.ag/(.*)-\d+\-(.*)",text)
        change_string = title.group(2)
        show_title = change_string.replace("-", " ")
        logging.info("Inserting new series %s" % show_title)
        cursor.execute('INSERT INTO series(title,' +
                           'series_link,' +
                           'number_of_episodes,' +
                           'number_of_seasons,' +
                           'status,' +
                           'current_season,' +
                           'last_update)' +
                           ' VALUES(?,?,0,0,1,0,?)', (show_title.title(), text, datetime.now(),))
        connection.commit()
        logging.debug("Series Added: "+show_title)
        link_box.set_text('')
        dialog.get_object('linkdialog').destroy()
    else:
        notice.set_text("Not a valid link or link already exists")
        notice.set_visible(True)
        dialog.get_object('imcheck').set_visible(True)
        logging.warn("Invalid link:"+text)


class Confirm:
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
        self.message, self.sql = which_sql_message(self.instruction)
        self.confirm.get_object('msgdlg').format_secondary_text(self.message+" " +
                                                                self.title+"?")
        self.confirm.get_object('msgdlg').show()

    def on_btnOk_clicked(self, widget):
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.cursor.execute(self.sql, (self.title,))
        self.connect.commit()
        self.confirm.get_object('msgdlg').destroy()
        logging.warn("Deleting: "+self.title)

    def on_btnCancel_clicked(self, widget):
        self.confirm.get_object('msgdlg').destroy()


def which_sql_message(Instruction):
    if Instruction == "start":
        use_sql = "UPDATE series SET status=1 where title=?"
        message = "Are you sure you want to start updating"
    elif Instruction == "stop":
        use_sql = "UPDATE series SET status=0 where title=?"
        message = "Are you sure you want to stop updating"
    elif Instruction == "delete":
            use_sql = "DELETE FROM series WHERE title=?"
            message = "Are you sure you want to delete"
    return message, use_sql


class Statistics:
    def __init__(self, title, connect, cursor):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/stats.glade")
        signals = {'on_btnClose_clicked': self.on_btnClose_clicked}
        self.builder.connect_signals(signals)
        set_stats(title, connect, cursor, self.builder)
        self.builder.get_object('win_stats').show()

    def on_btnClose_clicked(self, widget):
        self.builder.get_object("win_stats").destroy()


def set_stats(title, connect, cursor, builder):
    cursor.execute("Select series_link,number_of_episodes,number_of_seasons,last_update,status FROM series WHERE title=?",(title,))
    for data in cursor.fetchall():
        link = data[0]
        episodes = str(data[1])
        seasons = str(data[2])
        update = str(data[3])
        status = str(data[4])
    builder.get_object("title").set_text(title)
    builder.get_object('url').set_text(link)
    builder.get_object('episodes').set_text(episodes)
    builder.get_object('seasons').set_text(seasons)
    builder.get_object('update').set_text(update[:10])
    if status == '0':
        builder.get_object('status').set_text("Not Updating")
    else:
        builder.get_object('status').set_text("Updating")


class Preferences:
    def __init__(self, cursor, connect, thread, db_file):
        self.cursor = cursor
        self.connect = connect
        self.pref = Gtk.Builder()
        self.pref.add_from_file("ui/prefrences.glade")
        self.thread = thread
        self.db_file = db_file
        signals = {'on_btnSave_clicked': self.on_btnSave_clicked,
                 'on_btnCancel_clicked': self.on_btnCancel_clicked}
        self.pref.connect_signals(signals)
        self.interval = self.pref.get_object('txtInterval')
        self.get_interval()
        self.pref.get_object('pref').show()

    def get_interval(self):
        self.cursor.execute("SELECT value FROM config WHERE key='update_interval'")
        key = self.cursor.fetchone()
        value = int(key[0])/3600
        self.interval.set_text(str(value))

    def on_btnSave_clicked(self, widget):
        try:
            value = str(int(self.interval.get_text()) * 3600)
            self.cursor.execute("UPDATE config set value=? where key='update_interval'",
                                (value,))
            self.connect.commit()
            logging.warn("Stoping old thread and starting new thread")
            self.thread.stop()
            self.thread.join()
            new_thread = UpdateClass(self.db_file)
            new_thread.setDaemon(True)
            new_thread.start()
            logging.info("Interval updated to "+value + "seconds")
            logging.warn("New Thread started")
            self.pref.get_object('pref').destroy()

        except Exception as e:
            logging.info("unable to add value")
            logging.exception(e)
            Error('error.glade')

    def on_btnCancel_clicked(self, widget):
        self.pref.get_object('pref').destroy()


class Error:
    def __init__(self):
        self.error = Gtk.Builder()
        self.error.add_from_file("ui/error.glade")
        signals = {'on_btnOk_activate': self.on_btnOk_activate}
        self.error.connect_signals(signals)
        self.error.get_object('error').show()

    def on_btnOk_activate(self, widget):
        self.error.get_object('error').destroy()


class Current_Season:
    def __init__(self, cursor, connection, series_title):
        self.cursor = cursor
        self.connection = connection
        self.series_title = series_title
        self.current_season = Gtk.Builder()
        self.current_season.add_from_file("ui/set_season.glade")
        signals = {'on_btnApply_clicked': self.on_btnApply_clicked,
                 'on_btnCancel_clicked': self.on_btnCancel_clicked}
        self.current_season.connect_signals(signals)
        cur_sea = fetch_current_season(cursor, connection, series_title)
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


def fetch_current_season(cursor, connection, series_title):
    cursor.execute('SELECT current_season from series where title=?', (series_title,))
    no_season = cursor.fetchone()
    return str(no_season[0])
