# -*- coding: utf-8 -*-
import logging
import math
import random

from PIL import Image, ImageDraw
from .wallpaper_filter import WallpaperFilter
from ..geom.point import Point
from ..geom.size import Size

logger = logging.getLogger(__name__)


class Tunnel(WallpaperFilter):

    def _centroid(self, size) -> Point:
        return Point(size.width // 2, size.height // 2)

    def _filter(self, image: Image.Image, monitor: 'Monitor', position: Point) -> Image.Image:
        m_centre = self._centroid(monitor.size)
        i_centre = (Point(*position) + self._centroid(Size(*image.size)))

        angle = (math.degrees(-math.atan2(m_centre.y - i_centre.y, m_centre.x - i_centre.x)))
        if angle > 90:
            angle = 180 - angle
        if angle < -90:
            angle = 180 + angle

        logger.info('P1: %s, P2:%s, Angle: %s', m_centre, i_centre, angle)

        image = image.rotate(angle, expand=1, fillcolor=(0, 0, 0, 0))
        return image


class Jiggle(WallpaperFilter):

    def _filter(self, image: Image.Image, monitor: 'Monitor', position: Point) -> Image.Image:
        angle = 20 * random.random() - 10.0
        image = image.rotate(angle, expand=1, fillcolor=(0, 0, 0, 0))
        return image
