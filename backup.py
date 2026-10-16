"""Durable per-install file, setting and service-state backup."""
import datetime
import json
from pathlib import Path
import shutil
import subprocess

SERVICES = ['mpd.service', 'music-library-sync.service']


def systemctl(*args, check=True):
    return subprocess.run(['systemctl', '--user', *args], check=check, capture_output=True, text=True)


class Backup:
    def __init__(self, home, source):
        self.path = home/'.local/state/manjaro-music-kit/backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        self.path.mkdir(parents=True)
        self.manifest = {'files': [], 'settings': [], 'services': {}}
        shutil.copy2(source/'backup.py', self.path/'backup.py')
        (self.path/'restore.py').write_text('from pathlib import Path\nfrom backup import restore\nrestore(Path(__file__).resolve().parent)\n')
        self.save()

    def save(self):
        (self.path/'manifest.json').write_text(json.dumps(self.manifest, ensure_ascii=False, indent=2))

    def keep(self, path):
        if any(x['path'] == str(path) for x in self.manifest['files']): return
        exists = path.exists() or path.is_symlink()
        stored = str(len(self.manifest['files']))
        if exists:
            target = self.path/'files'/stored
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target, follow_symlinks=False)
        self.manifest['files'].append({'path': str(path), 'stored': stored, 'exists': exists})
        self.save()

    def write(self, path, text, executable=False):
        self.keep(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_symlink(): path.unlink()
        path.write_text(text)
        if executable: path.chmod(0o755)

    def record_services(self):
        for name in SERVICES:
            self.manifest['services'][name] = {
                'enabled': systemctl('is-enabled', name, check=False).stdout.strip(),
                'active': systemctl('is-active', name, check=False).stdout.strip() == 'active'}
        self.save()

    def setting(self, entry):
        self.manifest['settings'].append(entry)
        self.save()


def restore(path):
    manifest = json.loads((path/'manifest.json').read_text())
    for name in manifest['services']:
        systemctl('stop', name, check=False)
        systemctl('disable', name, check=False)
    for entry in reversed(manifest['files']):
        target = Path(entry['path'])
        if target.exists() or target.is_symlink(): target.unlink()
        if entry['exists']:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path/'files'/entry['stored'], target, follow_symlinks=False)
    for entry in reversed(manifest['settings']):
        if entry['type'] == 'xfconf':
            command = ['xfconf-query', '-c', 'xfce4-keyboard-shortcuts', '-p', entry['path']]
            command += ['--create', '-t', 'string', '-s', entry['value']] if entry['value'] is not None else ['--reset']
        else:
            command = ['dconf', 'write', entry['path'], entry['value']] if entry['value'] else ['dconf', 'reset', entry['path']]
        subprocess.run(command, check=True)
    systemctl('daemon-reload')
    for name, state in manifest['services'].items():
        if state['enabled'] in ('enabled', 'enabled-runtime'):
            systemctl('enable', *(['--runtime'] if state['enabled'] == 'enabled-runtime' else []), name)
        if state['active']: systemctl('start', name)
    print('已恢复本次安装前的配置、快捷键和服务启用状态；歌曲与系统安装的软件包没有删除。')
