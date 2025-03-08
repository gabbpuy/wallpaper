# -*- coding: utf-8 -*-
from typing import Optional

from PIL import Image
from rembg import remove

from .wallpaper_filter import WallpaperFilter
from ..geom.point import Point


class RemoveBackground(WallpaperFilter):
    def _filter(self, image: Image.Image, _monitor: Optional['Monitor'], _position: Point) -> Image.Image:
        try:
            image = remove(image)
        except Exception as e:
            pass
        return image
