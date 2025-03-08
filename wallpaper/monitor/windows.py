# -*- coding: utf-8 -*-
import ctypes
from ctypes import windll
import logging
from typing import Sequence

from wallpaper.monitor.monitor_rect import MonitorRect
from .monitor import Monitor

SysColour = windll.user32.GetSysColor(1)
logger = logging.getLogger(__name__)


class WindowsRect(ctypes.Structure):
    """
    Rectangle structure for EnumDisplayMonitors call
    """
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]

    def dump(self):
        f = (self.left, self.top, self.right, self.bottom)
        return MonitorRect(*[int(i) for i in f])


class WindowsMonitorInfo(ctypes.Structure):
    """
    monitor structure for EnumDisplayMonitors call
    """
    _fields_ = [
        ('cbSize', ctypes.c_ulong),
        ('rcMonitor', WindowsRect),
        ('rcWork', WindowsRect),
        ('dwFlags', ctypes.c_ulong)
    ]


def find_monitors() -> list:
    """
    Get the monitors connected to this machine
    """
    monitors = []
    callback_func = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(WindowsRect),
                                       ctypes.c_double)

    def callback(hMonitor, _hdcMonitor, lprcMonitor, _dwData) -> int:
        r = lprcMonitor.contents
        data = [hMonitor, r.dump()]
        monitors.append(data)
        return 1

    cbfunc = callback_func(callback)
    windll.user32.EnumDisplayMonitors(0, 0, cbfunc, 0)
    return monitors


def get_monitors(*_args, **_kwargs) -> Sequence[Monitor]:
    monitors = []
    for i, (hMonitor, extents) in enumerate(find_monitors()):
        logger.info('get_monitors() - %d: (%s, %s)', i, hMonitor, extents)
        mi = WindowsMonitorInfo()
        mi.cbSize = ctypes.sizeof(WindowsMonitorInfo)
        mi.rcMonitor = WindowsRect()
        mi.rcWork = WindowsRect()
        windll.user32.GetMonitorInfoA(hMonitor, ctypes.byref(mi))
        monitor = Monitor(hMonitor, mi.rcMonitor.dump(), mi.rcWork.dump(), mi.dwFlags, i)
        monitor.set_blend_colour(SysColour)
        monitors.append(monitor)
    return monitors
