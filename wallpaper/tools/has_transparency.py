# -*- coding: utf-8 -*-
import logging

from PIL import Image

logger = logging.getLogger(__name__)


def has_transparency(image: Image) -> bool:
    logger.info('Image: %s - %s, %s', image.info['filename'], image.mode, image.info.keys())
    if image.info.get('has_transparency') is not None:
        return True

    if image.mode == "RGBA":
        extrema = image.getextrema()
        if extrema[3][0] < 255:
            return True

    return False
