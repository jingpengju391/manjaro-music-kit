"""GUI smoke test: private D-Bus session, fake audio/playlist; no MPD changes.
Run: dbus-run-session -- python3 tests/smoke_player.py
"""
import importlib.util
import os
from pathlib import Path
import shutil
import socket
import threading
import tempfile

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='music-kit-smoke-') as directory:
    folder = Path(directory)
    for name in ['portable-player.py', 'spectrum-lines.py']:
        shutil.copy2(ROOT/'payload/ncmpcpp'/name, folder/name)
    server = socket.socket()
    server.bind(('127.0.0.1', 0)); server.listen()
    port = server.getsockname()[1]
    def serve():
        while True:
            try: conn, _ = server.accept()
            except OSError: return
            with conn:
                stream = conn.makefile('rwb', buffering=0)
                stream.write(b'OK MPD 0.24.0\n')
                request = stream.readline().strip()
                response = (b'state: pause\nsongid: 1\nelapsed: 45\nduration: 180\n' if request == b'status' else
                            b'file: demo.flac\nTitle: Music Kit Demo\nArtist: Test Artist\nId: 1\nduration: 180\n' if request == b'playlistinfo' else b'')
                stream.write(response + b'OK\n')
    threading.Thread(target=serve, daemon=True).start()
    (folder/'playlist-widget.py').write_text((ROOT/'payload/ncmpcpp/playlist-widget.py').read_text().replace('6600', str(port)).replace('@HOME@', str(folder)))
    (folder/'cava').write_text('#!/usr/bin/python3\nimport os,time\nwhile True:\n os.write(1,bytes(range(0,240,8)))\n time.sleep(.03)\n')
    (folder/'cava').chmod(0o755)
    os.environ['PATH'] = str(folder)+':'+os.environ['PATH']
    spec = importlib.util.spec_from_file_location('player', folder/'portable-player.py')
    player = importlib.util.module_from_spec(spec); spec.loader.exec_module(player)
    app = player.Player()
    errors = []
    def verify():
        try:
            assert app.window and app.window.get_visible(), 'window not visible'
            assert app.child_pid, 'VTE playlist did not spawn'
            assert app.bars.proc.poll() is None, 'spectrum process exited early'
            assert any(app.bars.values), 'spectrum frames not consumed'
            class ToggleCommand:
                def get_arguments(self): return ['music', 'ui-toggle']
            pid = app.child_pid
            app.do_command_line(ToggleCommand())
            assert not app.window.get_visible(), 'toggle did not hide'
            app.do_command_line(ToggleCommand())
            assert app.window.get_visible(), 'toggle did not show'
            assert app.child_pid == pid, 'toggle restarted playlist'
            window = app.window.get_window()
            pixbuf = player.Gdk.pixbuf_get_from_window(window, 0, 0, app.window.get_allocated_width(), app.window.get_allocated_height())
            pixbuf.savev('/tmp/music-kit-smoke.png', 'png', [], [])
        except Exception as error:
            errors.append(str(error))
        app.quit()
        return False
    player.GLib.timeout_add(1800, verify)
    result = app.run(['smoke', 'show'])
    assert app.bars.proc.poll() is not None, 'spectrum process leaked'
    assert not errors, errors
    assert result == 0, result
    server.close()
    print('PASS: window, real curses playlist with isolated MPD stub, spectrum rendering, cleanup')
