# -*- coding: utf-8 -*-
from typing import Sequence

from wallpaper.monitor.monitor_rect import MonitorRect
from .monitor import Monitor


def get_monitors(rect: MonitorRect = None) -> Sequence[Monitor]:
    if rect is None:
        import tkinter
        root = tkinter.Tk()
        rect = MonitorRect(0, 0, root.winfo_screenwidth(), root.winfo_screenheight())
        root.destroy()
    return Monitor("Generic", rect, rect, 1, 0),
