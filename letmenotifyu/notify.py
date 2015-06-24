#!/usr/bin/python3

from gi.repository import Notify


def announce(type_s, title, link=''):
    Notify.init("Letmenotifyu")
    announcement = Notify.Notification.new(type_s+'\n', title+'\n'+link,
                                             'dialog-information')
    announcement.show()

