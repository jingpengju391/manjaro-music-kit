#!/usr/bin/env python3
"""Install the portable desktop music configuration for the current user."""
import datetime,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
HOME_DIR=Path.home()
dry='--dry-run' in sys.argv
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
backup=HOME_DIR/'.local/state/manjaro-music-kit/backups'/stamp
mapping={ROOT/'payload/music':HOME_DIR/'.local/bin/music',ROOT/'payload/mpd.conf':HOME_DIR/'.config/mpd/mpd.conf'}
for p in (ROOT/'payload/ncmpcpp').rglob('*'):
 if p.is_file():mapping[p]=HOME_DIR/'.config/ncmpcpp'/p.relative_to(ROOT/'payload/ncmpcpp')
for source,target in mapping.items():
 content=source.read_text().replace('@HOME@',str(HOME_DIR))
 if source.suffix=='.py' or source.name=='music':compile(content,str(target),'exec')
 if dry:print('配置:',target);continue
 if target.exists():
  dest=backup/target.relative_to(HOME_DIR);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,dest)
 target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content)
 if source.suffix=='.py' or source.name=='music':target.chmod(0o755)
if dry:
 print('检查通过；未写配置、未安装依赖、未启动服务。');sys.exit()
for sub in ['.config/mpd/playlists','.ncmpcpp/lyrics','Music','.config/systemd/user']:(HOME_DIR/sub).mkdir(parents=True,exist_ok=True)
service=HOME_DIR/'.config/systemd/user/music-library-sync.service'
if service.exists():
 dest=backup/service.relative_to(HOME_DIR);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(service,dest)
service.write_text('''[Unit]
Description=Append newly indexed music to MPD queue
After=mpd.service
Requires=mpd.service
[Service]
ExecStart=/usr/bin/python3 "%h/.config/ncmpcpp/sync-library.py"
Restart=on-failure
RestartSec=2
[Install]
WantedBy=default.target
''')
shortcuts={'<Primary><Alt>m':'music','<Primary><Alt>p':'music toggle','<Primary><Alt>comma':'music prev','<Primary><Alt>period':'music next','<Primary><Alt>h':'music hide'}
old={}
if shutil.which('xfconf-query'):
 for key,cmd in shortcuts.items():
  prop='/commands/custom/'+key
  r=subprocess.run(['xfconf-query','-c','xfce4-keyboard-shortcuts','-p',prop],capture_output=True,text=True)
  old[prop]=r.stdout.strip() if r.returncode==0 else None
  args=['xfconf-query','-c','xfce4-keyboard-shortcuts','-p',prop]
  if r.returncode:args+=['-n','-t','string']
  subprocess.run(args+['-s',str(HOME_DIR/'.local/bin')+'/'+cmd],check=True)
 backup.mkdir(parents=True,exist_ok=True);(backup/'shortcuts.json').write_text(json.dumps(old,ensure_ascii=False,indent=2))
# Desktop entry also works when ~/.local/bin is not in the login shell PATH.
app=HOME_DIR/'.local/share/applications/manjaro-music-kit.desktop';app.parent.mkdir(parents=True,exist_ok=True)
if app.exists():
 dest=backup/app.relative_to(HOME_DIR);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(app,dest)
app.write_text('[Desktop Entry]\nType=Application\nName=桌面音乐\nExec="'+str(HOME_DIR/'.local/bin/music')+'"\nIcon=multimedia-player\nTerminal=false\nCategories=AudioVideo;Audio;\n')
for args in [['daemon-reload'],['enable','mpd.service','music-library-sync.service'],['restart','mpd.service'],['restart','music-library-sync.service']]:subprocess.run(['systemctl','--user']+args,check=True)
subprocess.run([str(HOME_DIR/'.local/bin/music')],check=True)
print('安装完成。快捷键 Ctrl+Alt+M；命令 ~/.local/bin/music；旧配置备份：',backup)
