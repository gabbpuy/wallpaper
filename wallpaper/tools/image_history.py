# -*- coding: utf-8 -*-
import io
import logging
import os
import sqlite3
import threading
import time

from wallpaper.tools.decorators import locked

logger = logging.getLogger(__name__)
DB_PATH = 'priorwalls.db'

osPath = os.path


class SQL_ImageHistory:

    def __init__(self):
        self.count = 0
        self._setup_db()
        self.priorWalls = self.load_walls()
        self.newWalls = set()
        self.count = 0

    @staticmethod
    def _setup_db():
        if not osPath.exists(DB_PATH):
            db = sqlite3.connect(DB_PATH)
            try:
                cursor = db.cursor()
                cursor.executescript(
                    """
                    CREATE TABLE dir_entries (
                        directory TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        last_used INTEGER NOT NULL);
                    CREATE INDEX dir_path ON dir_entries(directory);
                    """
                )
            finally:
                db.commit()
                db.close()

    @staticmethod
    def load_walls():
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        result = cursor.execute('SELECT directory, filename FROM dir_entries')
        return {
            os.path.join(r[0], r[1]) for r in result.fetchall()
        }

    def remove_walls(self, walls):
        self.priorWalls -= set(walls)
        path = os.path.dirname(walls[0])
        logging.info("DELETING :-) %s", path)
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        yesterday = int(time.time() - 86400)
        cursor.execute(
            'DELETE FROM dir_entries where directory = ? and last_used < ?', (path, yesterday)
        )
        db.commit()

    def add_wall(self, wall):
        if wall not in self.priorWalls:
            self.newWalls.add(wall)
        self.priorWalls.add(wall)

    def write_walls(self):
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        if self.newWalls and not self.count:
            cursor.executemany(
                "INSERT INTO dir_entries(directory, filename, last_used) VALUES (?, ?, strftime('%s', 'now'))",
                [os.path.split(wall) for wall in self.newWalls]
            )
            db.commit()

    def get_available(self, files, dontWant=()):
        return list(set(files) - self.priorWalls - dontWant)

    def bump(self):
        self.count += 1

    def un_bump(self):
        self.count -= 1

    def __enter__(self):
        self.bump()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.un_bump()


class FileImageHistory:
    """
    A brief history of previously used images
    """
    CacheLock = threading.RLock()

    def __init__(self):
        self.needsWrite = False
        self.priorWalls = self.load_walls()
        self.count = 0

    @staticmethod
    def load_walls():
        if osPath.exists('priorWalls.txt'):
            with io.open('priorWalls.txt', 'rt', encoding='utf-8') as fp:
                return set(f.strip() for f in fp)
        return set()

    @locked(CacheLock)
    def add_wall(self, wall):
        self.needsWrite = True
        self.priorWalls.add(wall)

    @locked(CacheLock)
    def write_walls(self):
        if self.needsWrite and not self.count:
            with io.open('priorWalls.txt', 'wt', encoding='utf-8') as fp:
                existing = sorted(w for w in self.priorWalls if osPath.exists(w))
                fp.write('\n'.join(existing))
            self.needsWrite = False

    @locked(CacheLock)
    def remove_walls(self, walls):
        if walls:
            self.priorWalls -= set(walls)
            self.needsWrite = True

    def get_available(self, files, dontWant=()):
        return list(set(files) - self.priorWalls - dontWant)

    @locked(CacheLock)
    def bump(self):
        self.count += 1

    @locked(CacheLock)
    def un_bump(self):
        self.count -= 1

    def __enter__(self):
        self.bump()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.un_bump()


ImageHistory = SQL_ImageHistory
