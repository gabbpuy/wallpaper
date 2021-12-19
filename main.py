# -*- coding: utf-8 -*-
from argparse import ArgumentParser
import logging
import os
import random

from wallpaper.desktop.windows_desktop import WindowsDesktop as Desktop
from wallpaper.config import WallpaperConfig


class Wallpaper:
    """
    The master wallpaper object
    """

    def __init__(self):
        self.config = None
        random.seed()

    def get_config_file_options(self, options):
        config_file = 'pywallpaper.json'
        if options.config_file:
            config_file = options.config_file
        self.config = WallpaperConfig()
        self.config.load(open(config_file, 'rt', encoding='utf-8'))

    @staticmethod
    def get_command_line_options():
        parser = ArgumentParser()
        parser.add_argument('--image', '-i', dest='single_image', default=None,
                            help='Set wallpaper to this image and exit (overrides -d)')
        parser.add_argument('--directory', '-d', dest='directories', default=[], action='append',
                            type=str, help='Add an image directory')
        parser.add_argument('--config', '-c', dest='config_file', default=None,
                            help='path to alternate config file (default <working dir>/pywallpaper.conf)')
        parser.add_argument('--working-dir', '-w', dest='cwd', default='.', help='Working Directory (default .)')
        parser.add_argument('--single_image', help='single image to set as wallpaper', default=None)
        return parser.parse_args()

    def go(self):
        options = self.get_command_line_options()
        if options.cwd:
            if options.cwd != '.':
                os.chdir(options.cwd)
        self.get_config_file_options(options)
        desktop = Desktop(self.config)
        if options.single_image:
            desktop.set_wallpaper_from_image(options.single_image)
        else:
            desktop.generate_wallpaper()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, filename='wallpaper.log')
    pil_logger = logging.getLogger('PIL')
    pil_logger.setLevel(logging.INFO)
    logging.info('Starting')
    d = Wallpaper()
    d.go()
