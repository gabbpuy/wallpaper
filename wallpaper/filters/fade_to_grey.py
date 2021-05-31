# -*- coding: utf-8 -*-
from PIL import Image

from .wallpaper_filter import WallpaperFilter
from ..geom.point import Point


class FadeToGrey(WallpaperFilter):
    def _filter(self, image: Image.Image, _monitor: 'Monitor', _position: Point) -> Image.Image:
        image = image.convert('RGB').convert('L')
        return image
