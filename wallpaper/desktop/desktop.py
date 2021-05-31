# -*- coding: utf-8 -*-
import logging
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageDraw, ImageFile

from wallpaper.config import WallpaperConfig, MonitorConfig
from wallpaper.geom.size import Size
from wallpaper.monitor import get_monitors, Monitor
from wallpaper.monitor.monitor_rect import MonitorRect
from wallpaper.filters.wallpaper_filter import WallpaperFilter

MID_GREY = (128, 128, 128)
DARK_GREY = (64, 64, 64)
ImageFile.MAXBLOCK = 2 ** 20
logger = logging.getLogger(__name__)


class Desktop:
    """
    Represents the desktop

    :param config: The :mod:`ConfigParser` object
    """

    def __init__(self, config: WallpaperConfig):
        self._master_monitor = None
        self.wallpaper_config: WallpaperConfig = config
        self.config: MonitorConfig = config.global_config

        self.monitors = []
        self.win_size = None

        self.bg_colour = (0, 0, 0)
        self.bg_image = None
        self.set_monitor_extents()
        self.create_empty_wallpaper()

    def load_current_wallpaper(self):
        pass

    def set_wallpaper(self):
        logger.info('Filters: %s', WallpaperFilter.list_filters())
        logger.info('Desktop Filters: %s', self.config.desktop_filters)

        for image_filter in self.config.desktop_filters:
            self.bg_image = WallpaperFilter.get_filter(image_filter)(self.bg_image)

    def calc_wallpaper_size(self) -> Size:
        """
        Work out the size and ordering of the monitors
        """
        # Also sets the relative offsets for building the wallpaper...
        ms = self.monitors

        width = max(m.right for m in ms)
        height = max(m.bottom for m in ms)

        extra_width = -min(m.left for m in ms)
        extra_height = -min(m.top for m in ms)

        width += extra_width
        height += extra_height

        return Size(width, height)

    def set_monitor_extents(self):
        """
        Set the monitor sizes, and positions
        """
        self.monitors = get_monitors()
        self.win_size = self.calc_wallpaper_size()
        sz = MonitorRect(0, 0, self.win_size.width, self.win_size.height)
        self._master_monitor = Monitor(-1, sz, sz, 0, 0)

    def create_empty_wallpaper(self):
        """
        Create an image representing the entire desktop
        """
        c = (0, 0, 0, 0)
        stack_mode = self.config.stack_mode or any(m.config.stack_mode for m in self.monitors)
        self.bg_colour = c
        self.bg_image = bgImage = Image.new('RGBA', tuple(self.win_size), c)

        if stack_mode:
            self.load_current_wallpaper()
            return

        if self.config.gradient:
            r, g, b, _a = c
            width, height = bgImage.size
            fh = float(height)

            if (r + g + b) / 3 < 64:
                r1, g1, b1 = MID_GREY
            else:
                r1, g1, b1, _a = c
                r, g, b = DARK_GREY

            rd = r1 - r
            gd = g1 - g
            bd = b1 - b

            rs = float(rd) / fh
            gs = float(gd) / fh
            bs = float(bd) / fh

            draw = ImageDraw.Draw(bgImage)
            for h in range(0, height):
                draw.line((0, h, width, h),
                          fill=(int(r1), int(g1), int(b1)))
                r1 -= rs
                b1 -= bs
                g1 -= gs

    def generate_wallpaper(self):
        """
        Generate a wallpaper, by telling each monitor to generate its
        wallpaper with its own settings. Assign a thread per monitor,
        so that monitors are done in parallel.
        """
        monitors = self.monitors if not self.config.spanning else [self._master_monitor, ]
        with ThreadPoolExecutor() as executor:
            for m in monitors:
                logging.debug(m)
                m.set_monitor_config(self.wallpaper_config.monitors.get(str(m.monitor_number), self.config))
                m.set_bg_image(self.bg_image)
                executor.submit(m.generate_wallpaper)

        self.set_wallpaper()

    def set_wallpaper_from_image(self, path_to_image):
        pass
