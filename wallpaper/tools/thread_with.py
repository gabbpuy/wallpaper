import threading


class ThreadWith(threading.Thread):
    """
    Yep
    """
    def start(self):
        super(ThreadWith, self).start()
        return self
