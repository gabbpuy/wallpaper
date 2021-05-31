# -*- coding: utf-8 -*-
import logging
from PIL import Image, ImageDraw
from .wallpaper_filter import WallpaperFilter
from ..geom.point import Point
from ..tools.has_transparency import has_transparency

logger = logging.getLogger(__name__)


class Border(WallpaperFilter):
    def _filter(self, image: Image.Image, _monitor: 'Monitor', _position: Point) -> Image.Image:
        if has_transparency(image):
            return image
        draw = ImageDraw.Draw(image)
        w, h = image.size
        rect = ((0, 0), (w - 1, h - 1))
        draw.rectangle(rect, outline=(0, 0, 0, 255))
        rect = self._shrink_rect(rect)
        draw.rectangle(rect, outline=(128, 128, 128, 255))
        return image
