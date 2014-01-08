
from gi.repository import Notify

def announce(*args):
    Notify.init("Letmenotifyu")
    if args[0] == "New Movie":
        movie_show = Notify.Notification.new(args[0]+'\n',args[1]+'\n'+args[2],
                                             'dialog-information')
        movie_show.show()
    else:
        series_show = Notify.Notification.new(args[0]+'\n', args[1]+'\n'+args[2],
                                              'dialog-information')
        series_show.show()


