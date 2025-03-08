# -*- coding: utf-8 -*-
import logging
import math
import random

from PIL import Image

from wallpaper.geom.point import Point
from wallpaper.geom.size import Size
from .wallpaper_filter import WallpaperFilter

logger = logging.getLogger(__name__)


class Tunnel(WallpaperFilter):

    @staticmethod
    def _centroid(size) -> Point:
        return Point(size.width // 2, size.height // 2)

    def _filter(self, image: Image.Image, monitor: 'Monitor', position: Point) -> Image.Image:
        # Calculate center points
        m_centre = self._centroid(monitor.size)
        i_centre = Point(*position) + self._centroid(Size(*image.size))

        # Calculate the angle needed to align the vertical axis
        angle = math.degrees(math.atan2(m_centre.x - i_centre.x, m_centre.y - i_centre.y))

        # Ensure image stays upright when it's below the monitor's horizontal center
        if i_centre.y > m_centre.y:
            # If image is below monitor center, adjust angle to keep it upright
            if angle > 0:
                angle = angle - 180
            else:
                angle = angle + 180

        # Log the rotation information
        logger.info('Monitor center: %s, Image center: %s, Rotation angle: %s degrees',
                    m_centre, i_centre, angle)

        # Rotate the image
        image = image.rotate(angle, expand=True, fillcolor=(0, 0, 0, 0))
        return image


class Jiggle(WallpaperFilter):

    def _filter(self, image: Image.Image, monitor: 'Monitor', position: Point) -> Image.Image:
        angle = 20 * random.random() - 10.0
        image = image.rotate(angle, expand=True, fillcolor=(0, 0, 0, 0))
        return image
