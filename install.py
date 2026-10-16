#!/usr/bin/env python3
"""Install on the logged-in Manjaro desktop; back up before every settings write."""
import argparse
import ast
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from backup import Backup, SERVICES, systemctl, restore
from desktop_support import detect, packages

ROOT = Path(__file__).resolve().parent


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def shortcuts(desktop, home, backup):
    actions = [('m', '', '打开音乐'), ('p', 'toggle', '播放暂停'), ('comma', 'prev', '上一首'),
               ('period', 'next', '下一首'), ('h', 'hide', '隐藏音乐')]
    if desktop == 'Xfce':
        for key, action, label in actions:
            path = '/commands/custom/<Primary><Alt>' + key
            old = subprocess.run(['xfconf-query', '-c', 'xfce4-keyboard-shortcuts', '-p', path], capture_output=True, text=True)
            # Never overwrite someone else's shortcut silently.
            value = shlex.join([str(home/'.local/bin/music')] + ([action] if action else []))
            if old.returncode == 0 and str(home/'.local/bin/music') not in old.stdout:
                print('保留已有快捷键：', key); continue
            backup.setting({'type': 'xfconf', 'path': path, 'value': old.stdout.strip() if old.returncode == 0 else None})
            subprocess.run(['xfconf-query', '-c', 'xfce4-keyboard-shortcuts', '-p', path, '--create', '-t', 'string', '-s', value], check=True)
    elif desktop == 'GNOME':
        schema = 'org.gnome.settings-daemon.plugins.media-keys'
        if schema not in command('gsettings', 'list-schemas').splitlines():
            print('此 GNOME 未提供媒体快捷键接口；请通过应用菜单打开。'); return
        raw_list = command('gsettings', 'get', schema, 'custom-keybindings')
        paths = ast.literal_eval(raw_list.removeprefix('@as '))
        base = '/org/gnome/settings-daemon/plugins/media-keys/'
        if command('gsettings', 'writable', schema, 'custom-keybindings') != 'true':
            print('GNOME 快捷键被系统策略锁定，跳过。'); return
        backup.setting({'type': 'dconf', 'path': base+'custom-keybindings', 'value': command('dconf', 'read', base+'custom-keybindings')})
        for key, action, label in actions:
            path = base + 'custom-keybindings/manjaro-music-kit-' + key + '/'
            custom = 'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:'
            binding = '<Control><Alt>' + key
            if any(command('gsettings', 'get', custom+p, 'binding').strip("'").replace('<Primary>', '<Control>') == binding for p in paths if p != path):
                print('保留已有 GNOME 快捷键：', binding); continue
            values = {'name': label, 'command': shlex.join([str(home/'.local/bin/music')] + ([action] if action else [])), 'binding': binding}
            if any(command('gsettings', 'writable', custom+path, k) != 'true' for k in values): continue
            for k, v in values.items():
                backup.setting({'type': 'dconf', 'path': path+k, 'value': command('dconf', 'read', path+k)})
                subprocess.run(['gsettings', 'set', custom+path, k, v], check=True)
            if path not in paths: paths.append(path)
        subprocess.run(['gsettings', 'set', schema, 'custom-keybindings', repr(paths)], check=True)
    else:
        print('KDE/其他桌面：应用菜单已提供播放器及播放控制；全局快捷键请在系统设置中按需分配，不改写 KGlobalAccel 私有配置。')


def main():
    parser = argparse.ArgumentParser(description='自动识别桌面并安装音乐配置；无需指定 KDE/Xfce/GNOME。')
    parser.add_argument('--check', '--dry-run', dest='check', action='store_true', help='只读检查，不安装依赖或修改配置')
    parser.add_argument('--no-launch', action='store_true', help='安装后不自动打开播放器或播放')
    parser.add_argument('--restore', nargs='?', const='latest', metavar='目录', help='恢复指定备份；省略目录恢复最新一次')
    parser.add_argument('--list-backups', action='store_true')
    args = parser.parse_args()
    if os.geteuid() == 0: raise SystemExit('请用普通桌面用户运行。')
    home = Path.home()
    state = home/'.local/state/manjaro-music-kit/backups'
    backups = sorted(p.parent for p in state.glob('*/manifest.json'))
    if args.list_backups:
        print('\n'.join(map(str, backups)) or '暂无新版可恢复备份。'); return
    if args.restore:
        if args.restore == 'latest' and not backups: raise SystemExit('没有新版可恢复备份。旧版备份需手动还原。')
        target = backups[-1] if args.restore == 'latest' else Path(args.restore).expanduser().resolve()
        print('恢复备份：', target)
        restore(target); return
    desktop, session, backend = detect()
    print(f'桌面：{desktop}；会话：{session}；界面：{backend}')
    if session not in ('x11', 'wayland'): raise SystemExit('请在已登录的图形桌面运行，不支持无桌面的 SSH/TTY 安装。')
    if not shutil.which('pacman'): raise SystemExit('此安装器面向使用 pacman 的 Manjaro / Arch Linux。')
    required = packages(backend)
    if desktop == 'GNOME': required += ['glib2', 'dconf']
    if desktop == 'Xfce' and 'xfconf' not in required: required += ['xfconf']
    missing = subprocess.run(['pacman', '-T', *required], capture_output=True, text=True)
    if missing.returncode not in (0, 127): raise SystemExit('依赖查询失败：'+missing.stderr)
    if missing.stdout.strip():
        if args.check: raise SystemExit('缺少依赖：\n'+missing.stdout+'运行 bash install.sh 可自动安装。')
        print('补齐依赖需要完整升级系统，pacman 会要求密码和确认；取消即停止。', flush=True)
        subprocess.run(['sudo', 'pacman', '-Syu', '--needed', *required], check=True)
    imports = "import gi,cairo,math; gi.require_version('Gtk','3.0'); from gi.repository import Gtk; assert Gtk.init_check()[0], '无法连接图形桌面'"
    if backend == 'portable': imports += "; gi.require_version('Vte','2.91'); from gi.repository import Vte"
    subprocess.run(['/usr/bin/python3', '-c', imports], check=True)
    systemctl('show-environment')
    for name in SERVICES:
        if systemctl('is-enabled', name, check=False).stdout.strip().startswith('masked'):
            raise SystemExit(name+' 已被屏蔽，请先确认是否允许启用，未写入配置。')
    if desktop == 'Xfce': command('xfconf-query', '-l')
    subprocess.run(['pactl', 'info'], stdout=subprocess.DEVNULL, check=True)
    config = Path(os.environ.get('XDG_CONFIG_HOME', str(home/'.config')))
    data = Path(os.environ.get('XDG_DATA_HOME', str(home/'.local/share')))
    mapping = {ROOT/'payload/music': home/'.local/bin/music', ROOT/'payload/mpd.conf': config/'mpd/mpd.conf', ROOT/'desktop_support.py': config/'ncmpcpp/desktop_support.py'}
    for p in (ROOT/'payload/ncmpcpp').rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts: mapping[p] = config/'ncmpcpp'/p.relative_to(ROOT/'payload/ncmpcpp')
    rendered = {}
    for source, target in mapping.items():
        content = source.read_text().replace('@HOME@/.config', str(config)).replace('@HOME@', str(home))
        if source.suffix == '.py' or source.name == 'music': compile(content, str(target), 'exec')
        content = content.replace('~/.config/mpd', str(config/'mpd'))
        rendered[target] = (content, source.suffix == '.py' or source.name == 'music')
    if args.check:
        print('检查通过；未修改配置、安装依赖或启动服务。'); return
    backup = Backup(home, ROOT)
    print('备份：', backup.path, flush=True)
    try:
        backup.record_services()
        # Preserve all target files before stopping the service or writing any config.
        for target in rendered: backup.keep(target)
        for name in SERVICES: systemctl('stop', name, check=False)
        for target, (content, executable) in rendered.items(): backup.write(target, content, executable)
        for directory in [config/'mpd/playlists', home/'.ncmpcpp/lyrics', home/'Music']: directory.mkdir(parents=True, exist_ok=True)
        unit = config/'systemd/user/music-library-sync.service'
        backup.write(unit, '[Unit]\nDescription=Music library queue sync\nAfter=mpd.service\nRequires=mpd.service\n[Service]\n'
                     f'ExecStart=/usr/bin/python3 "{config}/ncmpcpp/sync-library.py"\nRestart=on-failure\nRestartSec=2\n[Install]\nWantedBy=default.target\n')
        # Explicit configuration path also supports XDG_CONFIG_HOME in a user service.
        backup.write(config/'systemd/user/mpd.service.d/music-kit.conf',
                     f'[Service]\nExecStart=\nExecStart=/usr/bin/mpd --systemd "{config}/mpd/mpd.conf"\n')
        app = '[Desktop Entry]\nType=Application\nName=桌面音乐\n'
        app += f'Exec="{home}/.local/bin/music"\nIcon=multimedia-player\nTerminal=false\nCategories=AudioVideo;Audio;\nActions=Toggle;Previous;Next;Hide;\n'
        for key, action, name in [('Toggle','toggle','播放暂停'),('Previous','prev','上一首'),('Next','next','下一首'),('Hide','hide','隐藏')]:
            app += f'\n[Desktop Action {key}]\nName={name}\nExec="{home}/.local/bin/music" {action}\n'
        backup.write(data/'applications/manjaro-music-kit.desktop', app)
        shortcuts(desktop, home, backup)
        systemctl('daemon-reload')
        systemctl('enable', *SERVICES)
        systemctl('restart', 'mpd.service')
        systemctl('restart', 'music-library-sync.service')
        if not args.no_launch: subprocess.run([str(home/'.local/bin/music')], check=True)
    except Exception:
        print('安装未完成；恢复命令：python3 ' + shlex.quote(str(backup.path/'restore.py')), file=sys.stderr)
        raise
    print('安装完成。应用菜单 → 桌面音乐；歌曲放入 ~/Music。')
    print('一键恢复：bash install.sh --restore')
    if backend == 'portable': print('此桌面使用兼容窗口：歌单与频谱同窗，可移动和调整尺寸；不强制置底、定位或无边框。')


if __name__ == '__main__':
    try: main()
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        raise SystemExit('安装失败：'+str(error))
