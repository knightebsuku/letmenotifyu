
import threading
import time

from notifylib.update import Update

class UpdateClass(threading.Thread):
    def __init__(self,db_file):
        self.db_file = db_file
        threading.Thread.__init__(self)
        self.event = threading.Event()

    def run(self):
        while not self.event.is_set():
            update = Update(self.db_file)
            interval=update.get_interval()
            update.start_updates()
            self.event.wait(int(interval))
    def stop(self):
        self.event.set()
