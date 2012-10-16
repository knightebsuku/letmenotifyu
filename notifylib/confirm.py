#! /usr/bin/python

from gi.repository import Gtk
from pysqlite2 import dbapi2 as sqlite

class Confirm:
    def __init__(self,gladefile,title,series_db):
        self.title=title #url
        self.series_db=series_db
        self.confirm=Gtk.Builder()
        self.confirm.add_from_file(gladefile)
        dicts={'on_btnOk_clicked':self.on_btnOk_clicked,
               'on_btnCancel_clicked':self.on_btnCancel_clicked}
        self.confirm.connect_signals(dicts)
        self.confirm.get_object('msgdlg').format_secondary_text('Are you sure you want to delete:'+" "+ self.title)
        window=self.confirm.get_object('msgdlg')
        window.show()

    def on_btnOk_clicked(self,widget):
        connect=sqlite.connect(self.series_db)
        db=connect.cursor()
        db.execute("DELETE FROM series WHERE title=?",(self.title,))
        connect.commit()
        self.confirm.get_object('msgdlg').destroy()

    def on_btnCancel_clicked(self,widget):
        self.confirm.get_object('msgdlg').destroy()

        
        
