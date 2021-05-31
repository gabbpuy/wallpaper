from functools import wraps


def locked(lock):
    """
    Synchronization decorator.
    """
    def decorated(f):
        @wraps(f)
        def locked_function(*args, **kw):
            with lock:
                return f(*args, **kw)
        return locked_function
    return decorated
