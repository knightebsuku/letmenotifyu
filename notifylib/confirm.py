
from gi.repository import Gtk

class Confirm:
    def __init__(self, gladefile, title,instruction,cursor,connect):
        self.connect=connect
        self.cursor=cursor
        self.title = title
        self.instruction=instruction
        self.confirm = Gtk.Builder()
        self.confirm.add_from_file(gladefile)
        dicts = {'on_btnOk_clicked': self.on_btnOk_clicked,
               'on_btnCancel_clicked': self.on_btnCancel_clicked}
        self.confirm.connect_signals(dicts)
        self.message,self.sql=which_sql_message(self.instruction)
        self.confirm.get_object('msgdlg').format_secondary_text(self.message+" "+ self.title+"?")
        window = self.confirm.get_object('msgdlg')
        window.show()

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
