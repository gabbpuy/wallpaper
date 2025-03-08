# -*- coding: utf-8 -*-
import collections
import concurrent.futures
import logging
import os
from random import randint, choice
from typing import Callable

from PIL import Image

from .file_cache import DirectoryCache

logger = logging.getLogger(__name__)

osPath = os.path

# For quick filtering
FileCache: DirectoryCache | None = None
update: Callable | None = None


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


def choose_dir_lite(dirs) -> list:
    extensions = Image.registered_extensions()

    chosen = choice(dirs)
    if not chosen.startswith('+'):
        return chosen

    chosen = chosen[1:]

    while True:
        logger.info('Root Choice: %s', chosen)

        root, dirs, files = next(os.walk(chosen))
        if files:
            if not dirs or randint(1, 100) < 50:
                d = update(osPath.join(root, chosen),
                           [osPath.join(root, f) for f in files if os.path.splitext(f)[-1].lower() in extensions])
                return d
        if dirs:
            chosen = osPath.join(root, choice(dirs))
        else:
            break
    return []

def expand_dirs_lite(dirs):
    global FileCache, update
    if not FileCache:
        FileCache = DirectoryCache()
        update = FileCache.update
    return dirs


def get_new_image(directory: str, dont_want: set = None) -> Image.Image | None:
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
