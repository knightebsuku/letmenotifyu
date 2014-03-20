
from gi.repository import Notify

def announce(*args):
    Notify.init("Letmenotifyu")
    announcement = Notify.Notification.new(args[0]+'\n',args[1]+'\n'+args[2],
                                             'dialog-information')
    announcement.show()
