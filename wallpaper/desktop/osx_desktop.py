import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
import logging
import pathlib
import shutil

from AppKit import NSScreen, NSRect, NSURL, NSWorkspace, NSImageScaling, NSWorkspaceDesktopImageOptionKey
from PIL import Image

from wallpaper.monitor.monitor_rect import MonitorRect
from .desktop import Desktop
from ..filters.wallpaper_filter import WallpaperFilter
from ..monitor import Monitor

logger = logging.getLogger(__name__)


class OSX_Desktop(Desktop):
    """
    OSX specific desktop
    """
    def __init__(self, config):
        super().__init__(config)
        self._root_path = pathlib.Path('~/Library/Application Support/pywallpaper').expanduser()

    def _load_wallpapers(self):
        path = self._root_path
        if not path.exists() or not list(path.glob('*_[0-9].jpg')):
            path.mkdir(exist_ok=True)
        monitors = self.monitors
        for i, monitor in enumerate(monitors):
            # Make blank placeholder images
            image_path = (path / f'pywallpaper_{i}.jpg')
            img = Image.new('RGB', tuple(monitor.size))
            if image_path.exists():
                # Paste existing images to blank image, in case monitor size is different.
                existing = Image.open(str(image_path))
                img.paste(existing, (0, 0))
            img.save(image_path)
            img.close()

    def generate_wallpaper(self):
        self._load_wallpapers()
        monitors = self.monitors
        with ThreadPoolExecutor() as executor:
            for i, m in enumerate(monitors):
                logger.info("%s: %s", i, m)
                m.set_monitor_config(self.wallpaper_config.monitors.get(str(m.monitor_number), self.config))
                m.set_bg_image(Image.open(self._root_path / f'pywallpaper_{i}.jpg'))
                executor.submit(m.generate_wallpaper)
        self.set_wallpaper()

    def set_wallpaper(self):
        for i, screen in enumerate(NSScreen.screens()):
            wallpaper = self.monitors[i].bg_image
            for image_filter in self.config.desktop_filters:
                wallpaper = WallpaperFilter.get_filter(image_filter)(wallpaper)

            wallpaper_path = (self._root_path / f'pywallpaper_{i}.jpg')
            wallpaper.convert('RGB').save(wallpaper_path)
            wallpaper.close()

            # OSX doesn't reload the desktop if the filename doesn't change...
            # So make a temporary name and set it then set it again with the name we want.
            temp_name = self._root_path / f'{str(uuid.uuid4())}.jpg'
            try:
                original = os.readlink(wallpaper_path)
                shutil.move(original, temp_name)
                os.unlink(wallpaper_path)
            except OSError:
                shutil.move(wallpaper_path, temp_name)

            url = NSURL.fileURLWithPath_(str(temp_name))
            logger.info('wallpaper url: %s', url)
            options = {NSWorkspaceDesktopImageOptionKey: 2}
            (result, error) = NSWorkspace.sharedWorkspace().setDesktopImageURL_forScreen_options_error_(url, screen, options,
                                                                                                        None)
            os.symlink(temp_name, wallpaper_path)
            logger.info('Set it: %s, %s', result, error)
