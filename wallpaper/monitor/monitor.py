# -*- coding: utf-8 -*-
import heapq
import logging
import random
from concurrent.futures import ThreadPoolExecutor
from functools import total_ordering
from typing import Generator, Union, Optional, List

from PIL import Image, ImageDraw, ImageFilter

from wallpaper.config import MonitorConfig
from wallpaper.filters.wallpaper_filter import WallpaperFilter
from wallpaper.geom.point import Point
from wallpaper.geom.rect import Rect
from wallpaper.geom.size import Size
from wallpaper.tools.directory_tools import get_new_image, expand_dirs, choose_dir, flush_walls

logger = logging.getLogger(__name__)


# noinspection PyBroadException
@total_ordering
class Monitor:
    """
    A monitor and its extents
    """

    def __init__(self, monitor, physical, working, flags, monitorNumber):
        logger.info('__init__(%s, %s, %s, %s, %s)', monitor, physical, working, flags, monitorNumber)
        self.dirs = []
        self._stack_thread = None
        self.monitor_number = monitorNumber
        self.monitor = monitor
        self.physical = physical
        self.working = working
        self.blend_colour = 0

        top_left = Point(*self.physical[:2])
        size = Size(*self.get_size(*self.physical))

        self.physical_rect = Rect(top_left, size)
        self.relative_rect = Rect(Point(0, 0), size)

        self.is_primary = (flags != 0)

        # All this moves to desktop
        self.need_v_split = self.top < 0 < self.bottom
        self.need_h_split = self.left < 0 < self.right
        self.needs_split = self.need_v_split or self.need_h_split

        self.image_list = set()
        self.bg_colour = (0, 0, 0)
        self.config: MonitorConfig = MonitorConfig()

        self.threads = []
        self.path = None
        self.__bg_image = None
        self.bg_image = None
        self.__workers = ThreadPoolExecutor()

    @property
    def size(self):
        return self.physical_rect.size

    @property
    def width(self):
        return self.physical_rect.w

    @property
    def height(self):
        return self.physical_rect.h

    @property
    def left(self):
        return self.physical_rect.left

    @property
    def top(self):
        return self.physical_rect.top

    @property
    def right(self):
        return self.physical_rect.right

    @property
    def bottom(self):
        return self.physical_rect.bottom

    def set_blend_colour(self, blendColour):
        self.blend_colour = blendColour

    @staticmethod
    def get_size(left, top, right, bottom) -> Size:
        """
        What's our actual width and height
        """
        return Size(abs(right - left), abs(bottom - top))

    def __repr__(self):
        return ('extent: ' + str(self.physical) +
                ' :: size: ' + str(self.size) +
                ' :: primary: ' + str(self.is_primary) +
                ' :: needs_split: ' + str(self.needs_split) +
                ' :: ' + str(self.monitor_number))

    def __eq__(self, other):
        return self.physical.top == other.physical.top and self.physical.left == other.physical.left

    def __lt__(self, other):
        if self.physical.top == other.physical.top:
            return self.physical.left < other.physical.left
        return self.physical.top < other.physical.top

    def set_monitor_config(self, config: MonitorConfig):
        """
        Configurate ourselvezz
        """
        self.config = config
        logger.info('Config is %s', self.config.__dict__)
        self.dirs = expand_dirs(self.config.directories)

    def choose_dir(self, dirs):
        if not self.path or not self.config.single_folder_mode:
            self.path = choose_dir(dirs)
        return self.path

    def put_image_at(self, image: Image.Image, position: Point, size: Size, sizer):
        """
        Resize and place the image on the background

        :param image: The current image
        :param position: Where to place the image
        :param size: The final size
        :param sizer: The resize method
        """
        try:
            if self.config.stack_mode and random.random() < 0.33:
                return

            if any(s < self.config.stop_threshold for s in size):
                return

            try:
                image = image.convert("RGBA").resize(size, sizer)
            except Exception:
                logging.error("%s is corrupt: %s", image.filename, size)
                return

            for image_filter in self.config.image_filters:
                logger.info('Filter: %s', image_filter)
                image = WallpaperFilter.get_filter(image_filter)(image, self, position)

            if self.config.shadow_mode:
                # image = shadow(image, self.bg_image, position)
                pass

            if self.config.blending:
                x, y = position
                w, h = size
                box = (x, y, x + w, y + h)
                img1 = self.bg_image.crop(box)
                image = Image.blend(img1, image, self.config.blend_ratio)
            self.bg_image.paste(image, tuple(position), mask=image)
        except:
            logger.exception('put_image_at: %s', (image, position, size, sizer))

    def make_strips(self) -> List[Rect]:
        """
        Break up the monitor into sections
        """
        # 1111111
        # -+---+-
        # 2|333|4
        # 2|333|4
        # -+---+-
        # 5555555
        strips = []
        w4 = int(self.size.width * 0.18)
        h4 = int(self.size.height * 0.15)

        strips.append(
            Rect(Point(0, 0), Size(self.width, h4)))

        t = 0 + h4
        b = self.height - h4
        strips.append(
            Rect(Point(0, t), Size(w4, b)))

        strips.append(
            Rect(Point(w4, t), Size(self.width - w4, b)))

        strips.append(
            Rect(Point(self.width - w4, t), Size(self.width, b)))

        strips.append(
            Rect(Point(0, self.height - h4), Size(self.width, self.height)))

        return strips

    def build_spiral(self) -> Generator:
        """
        Break up the monitor into sections using the golden ratio
        """
        ratio = 1.61803398875
        rect = self.relative_rect.copy()
        xs = 0
        ys = 0

        while rect.w > self.config.stop_threshold and rect.h > self.config.stop_threshold:
            if rect.w > rect.h:
                val = int(rect.w // ratio)
                size = Size(val, rect.h)
                # Spiral inwards by alternating the side
                if not xs % 2:
                    r = Rect(rect.top_left, size)
                else:
                    r = Rect(Point(rect.right - val, 0), size)
                xs += 1
            else:
                val = int(rect.h // ratio)
                size = Size(rect.w, val)
                if not ys % 2:
                    r = Rect(rect.top_left, size)
                else:
                    r = Rect(Point(0, rect.bottom - val), size)
                ys += 1

            rs = rect - r
            yield r
            rect = rs[0]

    def build_swatches(self, max_regions: int = 10) -> List[Rect]:
        """
        Build the swatches. Cut up the screen into a series of non-overlapping rectangles.

        :param max_regions: The upper limit on the number of rectangles to produce
        :return: A list of rectangles for filling with images.
        """
        root = Rect(Point(0, 0), Size(self.size.width, self.size.height))

        low_w = self.size.width // 4
        low_h = self.size.height // 4
        first_w = random.randint(low_w, self.size.width)
        first_h = random.randint(low_h, self.height)
        x = random.randint(0, self.size.width - first_w)
        y = random.randint(0, self.size.height - first_h)
        region = Rect(Point(x, y), Size(first_w, first_h))

        regions = root - region
        swatches = [Rect(Point(x, y), Size(first_w, first_h))]
        regions = [(-r.area, r) for r in regions
                   if r.w >= self.config.stop_threshold * 4 and r.h >= self.config.stop_threshold * 4]
        heapq.heapify(regions)
        count = 0
        while regions and count < max_regions:
            area, region = heapq.heappop(regions)
            low_w = max(region.w // 4, self.config.stop_threshold)
            low_h = max(region.h // 4, self.config.stop_threshold)
            if low_h > region.h or low_w > region.w:
                continue
            first_w = random.randint(low_w, region.w)
            first_h = random.randint(low_h, region.h)
            if first_w == region.w:
                x = region.left
            else:
                x = random.randint(region.left, region.right - first_w)
            if first_h == region.h:
                y = region.top
            else:
                y = random.randint(region.top, region.bottom - first_h)
            rect = Rect(Point(x, y), Size(first_w, first_h))
            swatches.append(rect)
            results = region - rect
            results = ((-r.area, r) for r in results
                       if r.w >= self.config.stop_threshold * 4 and r.h >= self.config.stop_threshold * 4)
            for rect in results:
                heapq.heappush(regions, rect)
            count += 1
        return swatches

    def build_strips(self):
        """
        Build fillable strips and fill them
        """
        strips = []
        fill_mode = self.config.fill_mode
        if fill_mode == 'strip':
            strips = self.make_strips()
        elif fill_mode == 'spiral':
            strips = reversed(list(self.build_spiral()))
        elif fill_mode == 'swatch':
            strips = self.build_swatches()

        for strip in strips:
            logger.info(strip)
            self.build_collage(strip)
            # Reset to a new dir
            if self.config.reset_collage_folder:
                self.path = None

    def wait_for_workers(self):
        self.__workers.shutdown(wait=True)

    def place_image(self, image: Image.Image, rect: Rect) -> tuple:
        """
        Find the scale and position for this image

        :param image: The image at hand
        :param rect: Constraints for the  image
        """

        scale, (image_width, image_height) = self._get_max_size(image, rect.size)

        size = rect.size
        pos = Point(*rect.top_left)
        x, y = pos

        dX = size.width - image_width
        dY = size.height - image_height

        # If there's space, choose whether to slide the image
        # left/right or up/down
        slide = random.randint(0, 1)

        if not slide:
            if max(dX, dY) == dX:
                pos.x += image_width
            else:
                pos.y += image_height
        else:
            x += dX
            y += dY

        if max(dX, dY) == dX:
            size.width = dX
        else:
            size.height = dY

        rs_filter = Image.BICUBIC
        if scale < 1.0:
            rs_filter = Image.ANTIALIAS

        rect.top_left = pos

        return (x, y), (image_width, image_height), rs_filter

    def get_collage_image(self, rect: Rect) -> Image.Image:
        n_dirs = len(self.dirs)
        pixels4 = (rect.w * rect.h) // 4

        image = None
        while n_dirs and not image:
            path = self.choose_dir(self.dirs)
            if not path:
                n_dirs = 0
                continue
            image = get_new_image(path, self.image_list)
            if not image:
                self.path = None
                self.image_list = set()
                continue

            iPix = image.size[0] * image.size[1]
            if iPix < pixels4:
                image = None
                self.path = None
                continue
        return image

    def build_collage(self, rect: Rect):
        if not self.dirs:
            return

        stop_threshold = self.config.stop_threshold
        if len(self.dirs) == 1:
            # work around random
            self.dirs += self.dirs

        building = True
        while building:
            image = self.get_collage_image(rect)
            self.image_list.add(image.info['filename'])
            position, size, sizer = self.place_image(image, rect)
            region = (image, position, size, sizer)
            building = ((rect.size.width > stop_threshold) and
                        (rect.size.height > stop_threshold))
            if building:
                self.__workers.submit(self.put_image_at, *region)

    def generate_wallpaper(self, fill_modes: tuple = ('strip', 'spiral', 'swatch')):
        stack_mode = self.config.stack_mode
        fill_mode = self.config.fill_mode

        if stack_mode:
            def _blurBack(this):
                try:
                    # BLUR = 11
                    BLUR = 5
                    img = this.__bg_image.crop(this.physical).convert('RGBA').filter(ImageFilter.GaussianBlur(BLUR))
                    for bg_filter in this.config.background_filters:
                        img = WallpaperFilter.get_filter(bg_filter)(img, self, (0, 0))
                    this.__bg_image.paste(img, (self.physical.left, self.physical.top))
                except KeyError:
                    pass
            self.__workers.submit(_blurBack, self)
        try:
            if fill_mode in fill_modes:
                self.build_strips()
                return

            if fill_mode == 'collage':
                rect = Rect(Point(0, 0), self.size)
                self.build_collage(rect)
                return

            generated = False
            while not generated:
                generated = self.set_wallpaper_from_directory(self.choose_dir(self.dirs))
        except:
            logging.exception('%s', self.monitor_number)
        finally:
            self.wait_for_workers()
            if stack_mode:
                self.__bg_image.paste(self.bg_image, (self.physical.left, self.physical.top), mask=self.bg_image)
            flush_walls()

    def set_wallpaper_from_directory(self, path: str) -> bool:
        """
        Find an image, and set it into our wallpaper.

        :param path: A directory containing images
        """
        image = get_new_image(path)
        if image:
            self.add_wallpaper(image)
            return True
        return False

    def _get_max_size(self, image: Image.Image, size: Optional[Size] = None) -> tuple:
        size = tuple(size or self.physical_rect.size)

        if size == image.size:
            return 1.0, image.size

        width, height = size
        image_width, image_height = image.size

        h_scale = float(height) / float(image_height)
        w_scale = float(width) / float(image_width)

        if self.config.fill:
            scale = max(h_scale, w_scale)
        else:
            scale = min(h_scale, w_scale)

        new_size = Size(int(image_width * scale), int(image_height * scale))

        return scale, new_size

    def max_aspect_wallpaper(self, image: Image.Image) -> Image.Image:
        """
        Blow the image up as much as possible without exceeding the monitor
        bounds. If self.Fill is True then resize until the entire monitor is
        filled and crop the excess.

        :param image: A :mod:`Image.Image`
        """
        scale, new_size = self._get_max_size(image)
        width, height = self.size

        if self.config.fill:
            im_width, im_height = new_size
            x = int((im_width - width) / 2.0)
            y = int((im_height - height) / 2.0)
            bbox = (x, 0, width + x, height + y)
            image = image.crop(bbox)

        return image

    def set_bg_image(self, bgImage: Image.Image):
        """
        Set the global desktop image
        """
        self.bg_image = bgImage

        if self.config.blending:
            # Alpha blend the image with the current desktop colour
            # Or black if something goes wrong with getting the desktop colour
            self.bg_colour = ((self.blend_colour & 0xFF),
                              (self.blend_colour & 0xFF00) >> 8,
                              (self.blend_colour & 0xFF0000) >> 16)

            draw = ImageDraw.Draw(self.bg_image)
            draw.rectangle(self.physical, outline=self.bg_colour,
                           fill=self.bg_colour)

        if self.config.stack_mode:
            self.__bg_image = self.bg_image
            self.bg_image = Image.new('RGBA', tuple(self.size), (0, 0, 0, 0))

    def centre_image(self, size: Size) -> tuple:
        w, h = size
        win_w, win_h = self.size
        x = (win_w - w) / 2
        y = (win_h - h) / 2
        return x, y

    def add_wallpaper(self, wallpaper: Union[str, Image.Image]):
        if isinstance(wallpaper, str):
            wallpaper = Image.open(wallpaper)

        if self.config.pre_rotate:
            if wallpaper.size[0] < wallpaper.size[1]:
                wallpaper = wallpaper.rotate(90, Image.BICUBIC, expand=True)

        position, size, sizer = self.place_image(wallpaper, Rect(Point(0, 0), self.size))
        position = self.centre_image(size)

        region = (wallpaper, position, size, sizer)
        self.__workers.submit(self.put_image_at, *region)
