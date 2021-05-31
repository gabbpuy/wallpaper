# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import logging
import os
import queue
import sqlite3
import threading
from pickle import load, dump

from wallpaper.tools.dir_entry import DirEntry
from wallpaper.tools.image_history import ImageHistory
from wallpaper.tools.decorators import locked

osPath = os.path


class _Cache(metaclass=ABCMeta):

    @abstractmethod
    def get(self, path):
        pass

    @abstractmethod
    def flush(self):
        pass

    @abstractmethod
    def update(self, path, files=None, **kwargs):
        pass

    @abstractmethod
    def set(self, path, files):
        pass


class SQL_Cache(_Cache):
    CacheLock = threading.RLock()
    CacheQueue = queue.Queue()

    def __init__(self):
        self.dir_cache = {}
        self.history = ImageHistory()
        self.changed = False
        if not osPath.exists('dircache.db'):
            db = sqlite3.connect('dircache.db')
            cursor = db.cursor()
            cursor.executescript(
                """
                CREATE TABLE dir_entries (
                    directory TEXT NOT NULL,
                    file TEXT NOT NULL,
                    modified_time REAL NOT NULL 
                );
                CREATE INDEX dir_path ON dir_entries(directory);
                """
            )
            db.close()
        self.queue_thread = threading.Thread(target=self._set_db)
        self.queue_thread.start()
        # self.count()

    def count(self):
        db = sqlite3.connect('dircache.db')
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM dir_entries')
        logging.error("Cache Entries: %d", cursor.fetchone()[0])

    def get(self, path):
        if path not in self.dir_cache:
            db = sqlite3.connect('dircache.db')
            cursor = db.cursor()
            cursor.execute('SELECT path, modified_time FROM dir_entries WHERE path = ?', (path,))
            try:
                r = cursor.fetchone()
                if r:
                    self.dir_cache[path] = DirEntry(r[0], stat=r[1])
            except:
                logging.exception("QUERY FAILED %s", path)

        return self.dir_cache.get(path)

    def flush(self):
        SQL_Cache.CacheQueue.put(None)
        self.queue_thread.join()

    def update(self, path, files=None, stat=os.stat):
        if self.get(path) and self.dir_cache[path].stat == int(stat(path).st_mtime):
            return path
        return self.set(path, files)

    @staticmethod
    def _set_db():
        db = sqlite3.connect('dircache.db')
        while True:
            entry = SQL_Cache.CacheQueue.get()
            if entry is None:
                db.commit()
                db.close()
                break
            cursor = db.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO dir_entries (modified_time, path) VALUES(?, ?) 
                """, (entry.stat, entry.path)
            )

    def set(self, path, files):
        entry = DirEntry(path, files)
        self.dir_cache[path] = entry
        self.CacheQueue.put(entry)
        return path


class OnFileCache(_Cache):
    CacheLock = threading.RLock()

    def __init__(self):
        self.directory_cache = {}
        self.history = ImageHistory()
        self.changed = False
        if osPath.exists('dircache.txt'):
            try:
                self.directory_cache = load(open('dircache.txt', 'rb'))
            except os.error:
                pass
            except AttributeError:
                pass

    def get(self, path):
        return self.directory_cache.get(path)

    @locked(CacheLock)
    def set(self, dire, files):
        self.changed = True
        self.directory_cache[dire] = DirEntry(dire, files)
        return dire

    def update(self, path, files=None, stat=os.stat):
        if path in self.directory_cache and self.directory_cache.get(path).stat == stat(path).st_mtime:
            return path
        return self.set(path, files)

    @locked(CacheLock)
    def flush(self):
        if self.changed:
            dump(self.directory_cache, open('dircache.txt', 'wb'), -1)
            self.changed = False


class NullCache(_Cache):
    CacheLock = threading.RLock()

    def __init__(self):
        self.directory_cache = {}
        self.history = ImageHistory()

    def get(self, path):
        return self.directory_cache.get(path)

    @locked(CacheLock)
    def set(self, path, files):
        self.directory_cache[path] = DirEntry(path, files)
        return path

    def update(self, path, files=None, stat=os.stat):
        if path in self.directory_cache and self.directory_cache.get(path).stat == stat(path).st_mtime:
            return path
        return self.set(path, files)

    def flush(self):
        pass


DirectoryCache = NullCache
