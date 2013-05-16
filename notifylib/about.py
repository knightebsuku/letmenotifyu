#!/usr/bin/python


from gi.repository import Gtk

class About:
    def __init__(self,gladefile):
        about=Gtk.Builder()
        about.add_from_file(gladefile)
        window=about.get_object('abtdlg')
        window.run()
        window.destroy()
        
