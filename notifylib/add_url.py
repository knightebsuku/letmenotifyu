#!/usr/bin/python

from gi.repository import Gtk
from pysqlite2 import dbapi2 as sqlite

        
class Add_Series:
    def __init__(self,gladefile,cursor):
        self.cursor=cursor
        self.dialog=Gtk.Builder()
        self.dialog.add_from_file(gladefile)
        dict={'on_btnCancel_clicked':self.on_btnCancel_clicked,
              'on_btnOk_clicked':self.on_btnOk_clicked,
              'on_entlink_button_release_event':self.on_entlink_button_release_event}
        self.dialog.connect_signals(dict)
        self.window=self.dialog.get_object('linkdialog')
        self.window.show()

    def on_btnCancel_clicked(self,*args):
        self.dialog.get_object('linkdialog').destroy()

    def on_btnOk_clicked(self,widget):
        link_box=self.dialog.get_object('entlink')
        self.check_url(link_box.get_text()) 
        link_box.set_text('')
        
    def on_entlink_button_release_event(self,widget,event):
        if event.button==2:
            url_paste=self.dialog.get_object('entlink')
            url_paste.paste_clipboard()


    def check_url(self,text): #check there is text and valid url
        url='http://www.1channel.ch/'
        if text=="" or text[0:23] != url:
            self.dialog.get_object('lblNotice').set_visible(True)
            self.dialog.get_object('imcheck').set_visible(True)
        else:
            self.enter_link(text)
            self.dialog.get_object('lblNotice').set_visible(False)
            self.dialog.get_object('imcheck').set_visible(False)
            

        
    def enter_link(self,url):
        title=re.search("http://www.1channel.ch/(.*)-\d+\-(.*)",url)
        change_string=title.group(2)
        show_title=change_string.replace("-"," ")
        self.cursor.execute('INSERT INTO series(title,series_link,num_eps) VALUES(?,?,0)',(show_title,url,))
        
