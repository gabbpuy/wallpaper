# -*- coding: utf-8 -*-
import collections
import concurrent.futures
import logging
import os
from random import randint
from typing import Optional

from PIL import Image

from .file_cache import DirectoryCache

osPath = os.path

# For quick filtering
FileCache: DirectoryCache = None
update = None


def flush_walls():
    FileCache.history.write_walls()


def expand_dir_t(directory, newDirEntry):
    """
    Expand dirs in a thread.

    :param directory: Root directory
    :param newDirEntry: Callback
    """
    dirM = collections.deque()
    append = dirM.append
    extensions = Image.registered_extensions()
    try:
        for root, dirs, files in os.walk(directory):
            if files:
                update(root, [os.path.join(root, f) for f in files if os.path.splitext(f)[-1].lower() in extensions])
                append(root)
        newDirEntry((directory, dirM))
    except:
        logging.exception('expand_dir_t')


def expand_dirs(dirs):
    """
    Find all dirs, recurse down any path starting with '+'

    :param dirs: A list of dirs
    """
    global FileCache, update
    if not FileCache:
        FileCache = DirectoryCache()
        update = FileCache.update
    newDirs = (FileCache.update(d) for d in dirs if d[0] != '+' and osPath.exists(d))
    newDirs = [(d, (d,)) for d in newDirs if d]
    newDirEntry = newDirs.append
    with concurrent.futures.ThreadPoolExecutor() as pool:
        for path in (d[1:] for d in dirs if d[0] == '+' and osPath.exists(d[1:])):
            pool.submit(expand_dir_t, path, newDirEntry)

    FileCache.flush()
    return newDirs


def choose_dir(dirs):
    """
    Choose a directory from a tree
    """
    nDirs = len(dirs)
    dirs = dirs[randint(0, nDirs - 1)][1]
    nDirs = len(dirs)
    if nDirs:
        path = dirs[randint(0, nDirs - 1)]
        return path


def get_new_image(directory: str, dont_want: set = None) -> Optional[Image.Image]:
    """
    Get a new image from a directory

    :param dont_want:
    :param directory: A directory full of files
    """
    if dont_want is None:
        dont_want = set()
    files = FileCache.get(directory).files
    if files:
        with FileCache.history as cache:
            available_files = cache.get_available(files, dont_want)
            if not available_files:
                cache.remove_walls(files)
                dont_want.update(files)
                available_files = cache.get_available(files, dont_want)

            tries = 0
            while tries < 3 and available_files:
                idx = randint(0, len(available_files) - 1)
                filename = available_files[idx]
                cache.add_wall(filename)
                try:
                    image = Image.open(filename)
                    image.draft('RGBA', image.size)
                    image.info['filename'] = filename
                    return image
                except Exception as e:
                    available_files.remove(filename)
                tries += 1
    return None
