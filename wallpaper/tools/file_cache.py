# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import logging
import os
import queue
import sqlite3
import threading
from pickle import load, dump
from typing import Sequence

from wallpaper.tools.dir_entry import DirEntry
from wallpaper.tools.image_history import ImageHistory
from wallpaper.tools.decorators import locked

osPath = os.path


class _Cache(metaclass=ABCMeta):

    @abstractmethod
    def get(self, path: str) -> str:
        pass

    @abstractmethod
    def flush(self):
        pass

    @abstractmethod
    def update(self, path: str, files: Sequence[str] | None = None, **kwargs) -> str:
        pass

    @abstractmethod
    def set(self, path: str, files: Sequence[str] | None) -> str:
        pass


class SQL_Cache(_Cache):
    CacheLock = threading.RLock()
    CacheQueue = queue.Queue()

    def __init__(self):
        self.dir_cache = {}
        self.history = ImageHistory()
        self.changed = False
        self.queue_thread = threading.Thread(target=self._set_db)
        self.queue_thread.start()
        self._create_cache_db()

    def _create_cache_db(self):
        dircache_db = 'dircache.db'
        if not osPath.exists(dircache_db):
            self._create_cache_table()

    def _create_cache_table(self):
        db = self._db()
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
        db.commit()
        db.close()

    def _db(self) -> sqlite3.Connection:
        return sqlite3.connect(self.dircache_db)

    def count(self) -> int:
        db = self._db()
        cursor = db.cursor()
        count = cursor.execute('SELECT COUNT(*) FROM dir_entries').fetchone()[0]
        logging.error("Cache Entries: %d", count)
        return count

    def get(self, path: str) -> str:
        if path not in self.dir_cache:
            db = self._db()
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

    def update(self, path: str, files=None, stat=os.stat):
        if self.get(path) and self.dir_cache[path].stat == int(stat(path).st_mtime):
            return path
        return self.set(path, files)

    def _set_db(self):
        db = self._db()
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

    def set(self, path: str, files: Sequence[str] | None):
        entry = DirEntry(path, files)
        self.dir_cache[path] = entry
        self.CacheQueue.put(entry)
        return path


class OnFileCache(_Cache):
    CacheLock = threading.RLock()

    def __init__(self):
        self.directory_cache: dict[str, DirEntry] = {}
        self.history = ImageHistory()
        self.changed = False
        if osPath.exists('dircache.txt'):
            try:
                self.directory_cache = load(open('dircache.txt', 'rb'))
            except os.error:
                pass
            except AttributeError:
                pass

    def get(self, path: str) -> DirEntry:
        return self.directory_cache.get(path)

    @locked(CacheLock)
    def set(self, dire: str, files: Sequence[str] | None) -> str:
        self.changed = True
        self.directory_cache[dire] = DirEntry(dire, files)
        return dire

    def update(self, path: str, files: Sequence[str] | None = None, stat=os.stat) -> str:
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
        self.directory_cache: dict[str, DirEntry] = {}
        self.history = ImageHistory()

    def get(self, path: str) -> DirEntry:
        return self.directory_cache.get(path)

    @locked(CacheLock)
    def set(self, path: str, files: Sequence[str] | None) -> str:
        # self.directory_cache[path] = DirEntry(path, files)
        self.directory_cache[path] = DirEntry(path, None)
        return path

    def update(self, path, files: Sequence[str] | None = None, stat=os.stat) -> str:
        if path in self.directory_cache and self.directory_cache.get(path).stat == stat(path).st_mtime:
            return path
        return self.set(path, files)

    def flush(self):
        pass


DirectoryCache = NullCache
