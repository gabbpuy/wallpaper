# -*- coding: utf-8 -*-
import logging
from typing import Optional

from PIL import Image
from rembg import remove

from .wallpaper_filter import WallpaperFilter
from ..geom.point import Point

logger = logging.getLogger(__name__)


class RemoveBackground(WallpaperFilter):
    def _filter(self, image: Image.Image, _monitor: Optional['Monitor'], _position: Point) -> Image.Image:
        try:
            image = remove(image)
        except Exception:
            logger.exception('RemoveBackground failed')
        return image
