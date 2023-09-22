from dataclasses import dataclass
from AppKit import NSScreen, NSRect

from wallpaper.monitor.monitor import Monitor
from wallpaper.monitor.monitor_rect import MonitorRect


def NS_Rect_to_monitor_rect(ns_rect: NSRect) -> MonitorRect:
    """
    NS Rect to Monitor Rect

    :param ns_rect: A NSRect from an NSScreen object
    """
    x = ns_rect.origin.x
    y = ns_rect.origin.y
    return MonitorRect(*map(int, (x, y, x + ns_rect.size.width, y + ns_rect.size.height)))


def get_monitors(*_args, **_kwargs):
    """
    Find monitors
    """
    screens = NSScreen.screens()
    monitors = []
    for i, screen in enumerate(screens):
        left, top, right, bottom = NS_Rect_to_monitor_rect(screen.frame())
        right -= left
        left = 0
        bottom -= top
        top = 0
        physical = MonitorRect(left, top, right, bottom)

        monitors.append(
            Monitor(
                screen.localizedName(),
                physical,
                NS_Rect_to_monitor_rect(screen.visibleFrame()),
                i == 0,
                i
            )
        )
    return monitors
