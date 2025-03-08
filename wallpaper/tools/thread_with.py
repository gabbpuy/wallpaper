import threading


class ThreadWith(threading.Thread):
    """
    Yep
    """
    def start(self) -> threading.Thread:
        super(ThreadWith, self).start()
        return self
