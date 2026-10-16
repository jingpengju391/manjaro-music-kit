import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import backup
import desktop_support
import install


class DetectionTests(unittest.TestCase):
    def test_desktops_and_sessions(self):
        for desktop, session, backend in [('KDE', 'wayland', 'portable'), ('KDE', 'x11', 'portable'),
                ('GNOME', 'wayland', 'portable'), ('GNOME', 'x11', 'portable'), ('XFCE', 'x11', 'xfce-x11'),
                ('XFCE', 'wayland', 'portable')]:
            with self.subTest(desktop=desktop, session=session):
                self.assertEqual(desktop_support.detect({'XDG_CURRENT_DESKTOP': desktop, 'XDG_SESSION_TYPE': session})[2], backend)

    def test_wayland_wins_over_xwayland_display(self):
        self.assertEqual(desktop_support.detect({'WAYLAND_DISPLAY': 'wayland-0', 'DISPLAY': ':0'})[1], 'wayland')

    def test_dependency_split(self):
        self.assertIn('vte3', desktop_support.packages('portable'))
        self.assertNotIn('xdotool', desktop_support.packages('portable'))
        self.assertNotIn('xfce4-terminal', desktop_support.packages('portable'))
        self.assertIn('xdotool', desktop_support.packages('xfce-x11'))


class BackupTests(unittest.TestCase):
    def test_close_widgets_stops_only_recorded_script(self):
        with tempfile.TemporaryDirectory() as folder:
            script = Path(folder)/'playlist-widget.py'
            script.write_text('import time; time.sleep(60)')
            player = subprocess.Popen([sys.executable, str(script)])
            unrelated = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
            try:
                backup.close_widgets({'files': [{'path': str(script)}]})
                player.wait(timeout=3)
                self.assertIsNone(unrelated.poll())
            finally:
                for process in (player, unrelated):
                    if process.poll() is None: process.terminate()
                    process.wait(timeout=3)

    def test_restore_files_symlinks_settings_and_services(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            original = home/'original'; original.write_text('original')
            link = home/'link'; link.symlink_to('original')
            new = home/'new'
            b = backup.Backup(home, install.ROOT)
            b.write(link, 'changed'); b.write(new, 'new')
            self.assertEqual(original.read_text(), 'original')
            b.manifest['services'] = {'mpd.service': {'enabled': 'enabled', 'active': True},
                                      'music-library-sync.service': {'enabled': 'not-found', 'active': False}}
            b.setting({'type': 'dconf', 'path': '/test/key', 'value': ''})
            b.setting({'type': 'xfconf', 'path': '/test/key', 'value': None})
            with patch('backup.systemctl') as system, patch('backup.subprocess.run') as run:
                backup.restore(b.path)
                system.assert_any_call('enable', 'mpd.service')
                system.assert_any_call('start', 'mpd.service')
                run.assert_any_call(['dconf', 'reset', '/test/key'], check=True)
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.read_text(), 'original')
            self.assertFalse(new.exists())


class InstallerTests(unittest.TestCase):
    def test_kde_install_and_restore_without_xfconf(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            config = home/'config'; config.mkdir()
            existing = config/'mpd/mpd.conf'; existing.parent.mkdir()
            existing.write_text('original config\n')
            def service(*args, **kwargs):
                return subprocess.CompletedProcess(args, 0, 'disabled\n' if args[0] == 'is-enabled' else 'inactive\n', '')
            env = {'XDG_CONFIG_HOME': str(config), 'XDG_DATA_HOME': str(home/'data'), 'XDG_CURRENT_DESKTOP': 'KDE', 'XDG_SESSION_TYPE': 'wayland'}
            with patch.dict(os.environ, env), patch('pathlib.Path.home', return_value=home), \
                    patch('os.geteuid', return_value=1000), patch('shutil.which', return_value='/usr/bin/tool'), \
                    patch('install.systemctl', side_effect=service), patch('backup.systemctl', side_effect=service), \
                    patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0, '', '')) as run, \
                    patch.object(sys, 'argv', ['install.py', '--no-launch']), contextlib.redirect_stdout(io.StringIO()):
                install.main()
                self.assertFalse(any('xfconf-query' in call.args[0] for call in run.call_args_list))
                b = next((home/'.local/state/manjaro-music-kit/backups').iterdir())
                manifest = json.loads((b/'manifest.json').read_text())
                self.assertEqual(len(manifest['services']), 2)
                self.assertIn('--systemd', (config/'systemd/user/mpd.service.d/music-kit.conf').read_text())
                self.assertTrue((home/'data/applications/manjaro-music-kit.desktop').exists())
                backup.restore(b)
                self.assertEqual(existing.read_text(), 'original config\n')
                self.assertFalse((home/'.local/bin/music').exists())

    def test_gnome_shortcuts_back_up_before_each_write(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            b = backup.Backup(home, install.ROOT)
            def query(*args):
                if args[:2] == ('gsettings', 'list-schemas'):
                    return 'org.gnome.settings-daemon.plugins.media-keys'
                if args[:2] == ('gsettings', 'writable'): return 'true'
                if args[:2] == ('gsettings', 'get'): return '@as []'
                if args[:2] == ('dconf', 'read'): return ''
                raise AssertionError(args)
            def write(args, **kwargs):
                records = json.loads((b.path/'manifest.json').read_text())['settings']
                if args[3] == 'custom-keybindings':
                    self.assertEqual(len(records), 13)
                else:
                    self.assertTrue(records[-1]['path'].endswith('/'+args[3]))
                return subprocess.CompletedProcess(args, 0)
            with patch('install.command', side_effect=query), patch('install.subprocess.run', side_effect=write):
                install.shortcuts('GNOME', home, b)

    def test_check_never_installs_or_creates_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            with patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'KDE', 'XDG_SESSION_TYPE': 'wayland'}), \
                    patch('pathlib.Path.home', return_value=home), patch('os.geteuid', return_value=1000), \
                    patch('shutil.which', return_value='/usr/bin/tool'), \
                    patch('subprocess.run', return_value=subprocess.CompletedProcess([], 127, 'vte3\n', '')) as run, \
                    patch.object(sys, 'argv', ['install.py', '--check']), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit): install.main()
                self.assertEqual(len(run.call_args_list), 1)
                self.assertFalse((home/'.local').exists())

    def test_cancel_dependency_install_stops_before_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            with patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'KDE', 'XDG_SESSION_TYPE': 'wayland'}), \
                    patch('pathlib.Path.home', return_value=home), patch('os.geteuid', return_value=1000), \
                    patch('shutil.which', return_value='/usr/bin/tool'), \
                    patch('subprocess.run', side_effect=[subprocess.CompletedProcess([], 127, 'vte3\n', ''), subprocess.CalledProcessError(1, 'sudo')]), \
                    patch.object(sys, 'argv', ['install.py']), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(subprocess.CalledProcessError): install.main()
                self.assertFalse((home/'.local').exists())


if __name__ == '__main__': unittest.main()
