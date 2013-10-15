#!/usr/bin /python3

from gi.repository import Gtk


class Statistics:
    def __init__(self,glade,title,connect,cursor):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(glade)
        signals= {'on_btnClose_clicked':self.on_btnClose_clicked}
        self.builder.connect_signals(signals)
        set_stats(title,connect,cursor,self.builder)
        self.builder.get_object('win_stats').show()
        
    def on_btnClose_clicked(self,widget):
        print("ok")
        self.builder.get_object("win_stats").destroy()
        



def set_stats(title,connect,cursor,builder):
    cursor.execute("Select series_link,number_of_episodes,number_of_seasons,last_update,status FROM series WHERE title=?",(title,))
    for data in cursor.fetchall():
        link= data[0]
        episodes= str(data[1])
        seasons= str(data[2])
        update= str(data[3])
        status= str(data[4])
    builder.get_object("title").set_text(title)
    builder.get_object('url').set_text(link)
    builder.get_object('episodes').set_text(episodes)
    builder.get_object('seasons').set_text(seasons)
    builder.get_object('update').set_text(update[:10])
    if status=='0':
        builder.get_object('status').set_text("Not Updating")
    else:
        builder.get_object('status').set_text("Updating")
        
