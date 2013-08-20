#!/usr/bin/python3

import re
from gi.repository import Gtk


def check_url(text, notice,dialog,cursor,connection,link_box):
    if re.match(r'http://vodly.to', text):
        enter_link(text,cursor,connection,dialog,link_box)
    else:
        notice.set_text("Not a valid link")
        notice.set_visible(True)
        dialog.get_object('imcheck').set_visible(True)


def enter_link(url, cursor, connection,dialog,link_box):
    title = re.search(r"http://vodly.to/(.*)-\d+\-(.*)", url)
    change_string = title.group(2)
    show_title = change_string.replace("-", " ")
    try:
        cursor.execute('INSERT INTO series(title,series_link,number_of_episodes,number_of_seasons) VALUES(?,?,0,0)', (show_title, url,))
        connection.commit()
        link_box.set_text('')
    except Exception as e:
        #Will use python loggin to output to file to keep track of  erros and  changes
        print(e)
        dialog.get_object('lblNotice').set_text("Link already exists")
        dialog.get_object('lblNotice').set_visible(True)
        dialog.get_object('imcheck').set_visible(True)
                

class Add_Series:
    def __init__(self, gladefile, cursor, connection):
        self.cursor = cursor
        self.connection = connection
        self.dialog = Gtk.Builder()
        self.dialog.add_from_file(gladefile)
        connectors = {'on_btnCancel_clicked': self.on_btnCancel_clicked,
              'on_btnOk_clicked': self.on_btnOk_clicked,
              'on_entlink_button_release_event': self.on_entlink_button_release_event}
        self.dialog.connect_signals(connectors)
        self.notice = self.dialog.get_object('lblNotice')
        self.window = self.dialog.get_object('linkdialog')
        self.window.show()
        
    def on_btnCancel_clicked(self, widget):
        self.window.destroy()

    def on_btnOk_clicked(self, widget):
        self.link_box = self.dialog.get_object('entlink')
        self.check_url(self.link_box.get_text(),self.notice,self.dialog,self.link_box) 
        self.link_box.set_text('')
