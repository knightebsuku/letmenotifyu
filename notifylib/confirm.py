
import webbrowser
from gi.repository import Gtk
from threading import Thread


class Confirm:
    def __init__(self, gladefile, title,instruction,connect,cursor):
        self.connect=connect
        self.cursor=cursor
        self.title = title
        self.instruction=instruction
        self.confirm = Gtk.Builder()
        self.confirm.add_from_file(gladefile)
        signals = {'on_btnOk_clicked': self.on_btnOk_clicked,
               'on_btnCancel_clicked': self.on_btnCancel_clicked}
        self.confirm.connect_signals(signals)
        self.message,self.sql=which_sql_message(self.instruction)
        self.confirm.get_object('msgdlg').format_secondary_text(self.message+" "+ self.title+"?")
        self.confirm.get_object('msgdlg').show()

    def on_btnOk_clicked(self, widget):
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.cursor.execute(self.sql,(self.title,))
        self.connect.commit()
        self.confirm.get_object('msgdlg').destroy()

    def on_btnCancel_clicked(self, widget):
        self.confirm.get_object('msgdlg').destroy()

        
def which_sql_message(Instruction):
    if Instruction=="start":
         use_sql="UPDATE series SET status=1 where title=?"
         message="Are you sure you want to start updating"
    elif Instruction=="stop":
        use_sql="UPDATE series SET status=0 where title=?"
        message="Are you sure you want to stop updating"
    elif Instruction=="delete":
            use_sql="DELETE FROM series WHERE title=?"
            message="Are you sure you want to delete"
    return message,use_sql

class Torrent:
        def __init__(self,title,cursor,connect):
                self.title=title
                self.cursor=cursor
                self.connect=connect
                self.split_title=self.title.split("-")
                
        def kickass(self):
                self.cursor.execute("Select name from torrents where id=1")
                result=self.cursor.fetchone()
                webbrowser.open_new(result[0]+self.split_title[0])
                
        def isohunt(self):
                self.cursor.execute("SELECT name from torrents where id=3")
                result=self.cursor.fetchone()
                webbrowser.open_new(result[0]+self.split_title[0])
                
        def piratebay(self):
                self.cursor.execute("SELECT name FROM torrents where id=2")
                result=self.cursor.fetchone()
                webbrowser.open_new(result[0]+self.split_title[0])
                
        def online(self,dic):
                webbrowser.open_new(dic[self.title])

                
def check_updates(thread,db_file):
        if thread.isAlive():
                print("Thread is still running")
                pass
        else:
                print("Starting new Thread")
                update_thread = Thread(target=get_updates,args=(self.db_file,))
                update_thread.setDaemon(True)
                update_thread.start()
                
