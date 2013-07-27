#!/usr/bin/python

import re
from gi.repository import Gtk

class Add_Series:
    def __init__(self, gladefile, cursor, connection):
        self.cursor = cursor
        self.connection = connection
        self.dialog = Gtk.Builder()
        self.dialog.add_from_file(gladefile)
        dict={'on_btnCancel_clicked': self.on_btnCancel_clicked,
              'on_btnOk_clicked': self.on_btnOk_clicked,
              'on_entlink_button_release_event': self.on_entlink_button_release_event}
        self.dialog.connect_signals(dict)
        self.notice = self.dialog.get_object('lblNotice')
        self.window = self.dialog.get_object('linkdialog')
        self.window.show()
        
    def on_btnCancel_clicked(self, *args):
        self.window.destroy()

    def on_btnOk_clicked(self, widget):
        self.link_box = self.dialog.get_object('entlink')
        self.check_url(self.link_box.get_text()) 
        self.link_box.set_text('')
        
    def on_entlink_button_release_event(self, widget, event):
        if event.button == 2:
            url_paste = self.dialog.get_object('entlink')
            url_paste.paste_clipboard()


    def check_url(self, text):
        if re.findall(r'(http://www.primewire.ag)|(http://www.1channel.ch)', text):
            self.enter_link(text)
            
        else:
                self.notice.set_text("Not a valid link")
                self.notice.set_visible(True)
                self.dialog.get_object('imcheck').set_visible(True)
        
    def enter_link(self, url):
        title=re.search(r"http://www.primewire.ag/(.*)-\d+\-(.*)", url)
        change_string=title.group(2)
        show_title=change_string.replace("-", " ")
        try:
                self.cursor.execute('INSERT INTO series(title,series_link,number_of_episodes,number_of_seasons) VALUES(?,?,0,0)', (show_title, url,))
                self.connection.commit()
                self.link_box.set_text('')
        except Exception:
                self.dialog.get_object('lblNotice').set_text("Link already exists")
                self.dialog.get_object('lblNotice').set_visible(True)
                self.dialog.get_object('imcheck').set_visible(True)
                
        
        
        
