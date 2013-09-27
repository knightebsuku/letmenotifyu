#!/usr/bin/python3


from gi.repository import Gtk
from notifylib.confirm import Confirm

class Delete_Series:
    def __init__(self, series_title, cursor, connect, gladefile):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        signals = {'on_DeleteSeries_select': self.on_Delete_Series_select,
                  'on_Update_select': self.on_Update_select}
        self.builder.connect_signals(signals)
        self.show_window = self.builder.get_object("Series").show()


    def on_Delete_Series_select(self, widget):
        Confirm('confirm7.glade', series_title, cursor, connect)
            
                                   
        
