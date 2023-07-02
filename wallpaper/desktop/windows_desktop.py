# -*- coding: utf-8 -*-
from ctypes import windll
import os
import logging
import winreg

import ntsecuritycon as con
from PIL import Image
from win32con import *
from win32 import win32security

from wallpaper.monitor.monitor_rect import MonitorRect
from .desktop import Desktop


user32 = windll.user32
logger = logging.getLogger(__name__)


class WindowsDesktop(Desktop):
    """
    Windows Features
    """

    def load_current_wallpaper(self):
        """
        Attempt to load the current wallpaper from disk
        """
        try:
            r = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            bgKey = r'Control Panel\Desktop'
            i = winreg.OpenKey(r, bgKey)
            wp = winreg.QueryValueEx(i, 'Wallpaper')
            img = Image.open(wp[0])
            self.bg_image.paste(img, (0, 0))
        except:
            logger.exception('LoadCurrent')

    @staticmethod
    def set_wallpaper_style_single():
        """
        Set the wallpaper for a single monitor
        """
        k = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r'Control Panel\Desktop', 0, winreg.KEY_WRITE)
        winreg.SetValue(k, 'WallpaperStyle', winreg.REG_SZ, '0')
        winreg.SetValue(k, 'TileWallpaper', winreg.REG_SZ, '0')

    @staticmethod
    def set_wallpaper_style_multi():
        """
        Set the wallpaper for multiple monitor configuration
        """
        # To set a multi-monitor wallpaper, we need to tile it...
        k = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r'Control Panel\Desktop', 0, winreg.KEY_WRITE)
        winreg.SetValue(k, 'WallpaperStyle', winreg.REG_SZ, '0')
        winreg.SetValue(k, 'TileWallpaper', winreg.REG_SZ, '1')

    @staticmethod
    def set_windows_permissions(filename):
        everyone, _domain, _type = win32security.LookupAccountName('', 'Everyone')
        dacl = win32security.ACL()
        dacl.AddAccessAllowedAce(win32security.ACL_REVISION,
                                 con.FILE_ALL_ACCESS, everyone)

        sd = win32security.GetFileSecurity(filename,
                                           win32security.DACL_SECURITY_INFORMATION)

        sd.SetSecurityDescriptorDacl(1, dacl, 0)


    def set_wallpaper_from_image(self, path_to_image):

        """
        Given a path to a bmp, set it as the wallpaper

        :param path_to_image: Set the windows wallpaper
        """
        # Set it and make sure windows remembers the wallpaper we set.
        result = user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0,
            path_to_image,
            SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE)
        if not result:
            raise Exception('Unable to set wallpaper.')

    def set_wallpaper(self):
        """
        Set the wallpaper
        """
        super().set_wallpaper()
        self.set_wallpaper_style()
        # Save the new wallpaper in our current directory.
        new_path = os.getcwd()
        new_path = os.path.join(new_path, 'pywallpaper.jpg')
        self.bg_image.convert('RGB').save(new_path, 'JPEG', quality=90)
        self.set_wallpaper_from_image(new_path)

    def set_wallpaper_style(self):
        """
        If we have multiple monitors, set the style to "Tiled", otherwise
        we want to set tiling off
        """
        if len(self.monitors) > 1:
            self.set_wallpaper_style_multi()
        else:
            self.set_wallpaper_style_single()

    def set_monitor_extents(self):
        super().set_monitor_extents()
        for monitor in (m for m in self.monitors if not m.is_primary):
            logger.info('set_monitor_extents() -> Initial: %s', monitor)
            if (not monitor.needs_split) and (monitor.physical.left < 0 or monitor.physical.top < 0):
                left, top, right, bottom = monitor.physical
                if left < 0:
                    left += self._master_monitor.physical.right
                    right += self._master_monitor.physical.right
                if top < 0:
                    top += self._master_monitor.physical.bottom
                    bottom += self._master_monitor.physical.bottom
                physical = MonitorRect(left, top, right, bottom)
                logger.info(physical)
                monitor.physical = physical
                logger.info('set_monitor_extents() --> Final: %s', monitor)
