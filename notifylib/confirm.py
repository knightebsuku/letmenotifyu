#! /usr/bin/python

from gi.repository import Gtk

class Confirm:
    def __init__(self, gladefile, title, cursor, connection):
        self.title = title
        self.cursor = cursor
        self.connection = connection
        self.confirm = Gtk.Builder()
        self.confirm.add_from_file(gladefile)
        dicts={'on_btnOk_clicked': self.on_btnOk_clicked,
               'on_btnCancel_clicked': self.on_btnCancel_clicked}
        self.confirm.connect_signals(dicts)
        self.confirm.get_object('msgdlg').format_secondary_text('Are you sure you want to delete:'+" "+ self.title)
        window=self.confirm.get_object('msgdlg')
        window.show()

    def on_btnOk_clicked(self, widget):
        self.cursor.execute("DELETE FROM series WHERE title=?", (self.title,))
        self.connection.commit()
        self.confirm.get_object('msgdlg').destroy()

    def on_btnCancel_clicked(self, widget):
        self.confirm.get_object('msgdlg').destroy()

        
        
