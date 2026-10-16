#!/usr/bin/python3
"""Native GTK/VTE player for KDE, GNOME and Wayland; no X11 window commands."""
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Gdk, Gio, GLib, Pango, Vte

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('spectrum', ROOT/'spectrum-lines.py')
spectrum = importlib.util.module_from_spec(spec)
spec.loader.exec_module(spectrum)


class Bars(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_size_request(182, 164)
        self.buf = b''
        self.values = [0.0] * 30
        self.target = [0.0] * 30
        self.connect('draw', lambda widget, context: spectrum.Spectrum.draw(self, widget, context))
        env = os.environ.copy()
        env.pop('LD_LIBRARY_PATH', None)
        self.proc = subprocess.Popen(['cava', '-p', str(ROOT/'cava-lines.conf')],
                                     stdout=subprocess.PIPE, env=env)
        os.set_blocking(self.proc.stdout.fileno(), False)
        self.timer = GLib.timeout_add(16, self.tick)

    def tick(self):
        if self.proc.poll() is not None:
            self.timer = None
            return False
        return spectrum.Spectrum.tick(self)

    def close(self):
        if self.timer: GLib.source_remove(self.timer)
        if self.proc.poll() is None:
            self.proc.terminate()
            try: self.proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.proc.kill(); self.proc.wait()
        self.proc.stdout.close()


class Player(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='io.github.manjaro_music_kit.Player',
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.window = None
        self.bars = None
        self.child_pid = None

    def do_command_line(self, command):
        if 'hide' in command.get_arguments()[1:]:
            self.quit()
        else:
            self.activate()
        return 0

    def do_activate(self):
        if self.window:
            self.window.present()
            return
        Gtk.Settings.get_default().set_property('gtk-application-prefer-dark-theme', True)
        self.window = Gtk.ApplicationWindow(application=self, title='桌面音乐')
        self.window.set_default_size(620, 240)
        self.window.connect('delete-event', lambda *args: (self.quit(), False)[1])
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(10)
        self.window.add(box)
        controls = Gtk.Box(spacing=6)
        box.pack_start(controls, False, False, 0)
        for label, action in [('上一首', 'prev'), ('播放 / 暂停', 'toggle'), ('下一首', 'next'), ('扫描音乐库', 'show')]:
            button = Gtk.Button(label=label)
            button.connect('clicked', self.control, action)
            controls.pack_start(button, False, False, 0)
        content = Gtk.Box(spacing=10)
        box.pack_start(content, True, True, 0)
        self.bars = Bars()
        content.pack_start(self.bars, False, False, 0)
        self.terminal = Vte.Terminal()
        self.terminal.set_font(Pango.FontDescription('Monospace 10'))
        self.terminal.set_size(50, 11)
        self.terminal.set_scrollback_lines(0)
        foreground = Gdk.RGBA(); foreground.parse('#e5ddd9')
        background = Gdk.RGBA(); background.parse('#252127')
        self.terminal.set_colors(foreground, background, [])
        self.terminal.set_audible_bell(False)
        content.pack_start(self.terminal, True, True, 0)
        self.terminal.connect('child-exited', self.child_exited)
        self.terminal.spawn_async(Vte.PtyFlags.DEFAULT, str(Path.home()),
            ['/usr/bin/python3', str(ROOT/'playlist-widget.py')], ['TERM=xterm-256color'],
            GLib.SpawnFlags.DEFAULT, None, None, -1, Gio.Cancellable(), self.spawned, self)
        hint = Gtk.Label(label='将歌曲放入 ~/Music · 回车播放 · 空格暂停 · 2 音乐库 · 关闭窗口继续播放')
        box.pack_start(hint, False, False, 0)
        self.window.show_all()
        self.terminal.grab_focus()

    def control(self, button, action):
        subprocess.Popen([str(Path.home()/'.local/bin/music'), action])
        self.terminal.grab_focus()

    def spawned(self, terminal, pid, error, data):
        if error:
            print('歌单启动失败：', error, file=sys.stderr)
            self.quit()
        else:
            self.child_pid = pid

    def child_exited(self, terminal, status):
        self.child_pid = None
        self.quit()

    def do_shutdown(self):
        if self.bars: self.bars.close()
        if self.child_pid:
            try: os.kill(self.child_pid, signal.SIGHUP)
            except ProcessLookupError: pass
        Gtk.Application.do_shutdown(self)


if __name__ == '__main__':
    raise SystemExit(Player().run(sys.argv))
