# -*- coding: utf-8 -*-
from PIL import Image
from .wallpaper_filter import WallpaperFilter
from ..geom.point import Point


class Sepia(WallpaperFilter):
    def _filter(self, image: Image.Image, _monitor: 'Monitor', _position: Point) -> Image.Image:
        width, height = image.size

        pixels = image.load()

        for py in range(height):
            for px in range(width):
                r, g, b, a = image.getpixel((px, py))
                tr = min(255, int(0.393 * r + 0.769 * g + 0.189 * b))
                tg = min(255, int(0.349 * r + 0.686 * g + 0.168 * b))
                tb = min(255, int(0.272 * r + 0.534 * g + 0.131 * b))
                pixels[px, py] = (tr, tg, tb, a)
        return image
