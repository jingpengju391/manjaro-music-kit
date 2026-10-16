"""Shared desktop/session detection; never infer X11 from a Wayland DISPLAY."""
import os


def detect(env=None):
    env = os.environ if env is None else env
    name = (env.get('XDG_CURRENT_DESKTOP', '') + ':' + env.get('DESKTOP_SESSION', '')).lower()
    desktop = next((label for words, label in [(('kde', 'plasma'), 'KDE Plasma'),
                    (('xfce',), 'Xfce'), (('gnome',), 'GNOME')]
                    if any(w in name for w in words)), '其他桌面')
    session = env.get('XDG_SESSION_TYPE') or ('wayland' if env.get('WAYLAND_DISPLAY') else 'x11' if env.get('DISPLAY') else 'unknown')
    backend = 'xfce-x11' if desktop == 'Xfce' and session == 'x11' else 'portable'
    return desktop, session, backend


def packages(backend):
    common = ['mpd', 'ncmpcpp', 'cava', 'python', 'python-gobject', 'python-cairo', 'gtk3', 'dbus', 'libpulse']
    if backend == 'xfce-x11':
        return common + ['xfce4-terminal', 'xdotool', 'xorg-xprop', 'xorg-xrandr', 'libx11', 'libxext', 'xfconf']
    return common + ['vte3']
