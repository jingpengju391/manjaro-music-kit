#!/usr/bin/python3
import fcntl,os,socket,sys,time
class MPD:
 def __init__(self):
  self.s=socket.create_connection(('127.0.0.1',6600),timeout=5)
  self.s.settimeout(None);self.f=self.s.makefile('rwb',buffering=0)
  if not self.f.readline().startswith(b'OK MPD'):raise RuntimeError('MPD greeting failed')
 def command(self,cmd):
  self.f.write((cmd+'\n').encode());out=[]
  while True:
   raw=self.f.readline()
   if not raw:raise ConnectionError('MPD disconnected')
   line=raw.decode().rstrip('\n')
   if line=='OK':return out
   if line.startswith('ACK'):raise RuntimeError(line)
   out.append(line)
 def close(self):self.f.close();self.s.close()
def sync():
 with open(os.environ.get('XDG_RUNTIME_DIR','/run/user/'+str(os.getuid()))+'/music-library-sync.lock','w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  m=MPD()
  try:
   queued={v[6:] for v in m.command('playlistinfo') if v.startswith('file: ')}
   for v in m.command('listall'):
    if v.startswith('file: ') and v[6:] not in queued:
     path=v[6:];m.command('add "'+path.replace('\\','\\\\').replace('"','\\"')+'"');queued.add(path)
     print('Added:',path,flush=True)
  finally:m.close()
if '--once' in sys.argv:sync()
else:
 while True:
  listener=None
  try:
   listener=MPD();sync()
   while True:
    listener.command('idle database');sync()
  except (OSError,RuntimeError) as e:
   print(str(e),flush=True);time.sleep(2)
  finally:
   if listener:listener.close()
