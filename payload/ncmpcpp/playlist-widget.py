#!/usr/bin/python3
"""Compact MPD queue: reserve time column and ellipsize display only."""
import curses,socket,time,unicodedata,os

def request(command):
 with socket.create_connection(('127.0.0.1',6600),timeout=2) as s:
  f=s.makefile('rwb',buffering=0);f.readline();f.write((command+'\n').encode());out=[]
  while True:
   raw=f.readline()
   if not raw:raise ConnectionError('MPD disconnected')
   line=raw.decode().rstrip('\n')
   if line=='OK':return out
   if line.startswith('ACK'):raise RuntimeError(line)
   out.append(line)
def values(lines):return dict(line.split(': ',1) for line in lines if ': ' in line)
def width(s):return sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in s)
def shorten(s,n):
 s=''.join(c for c in s if c.isprintable())
 if width(s)<=n:return s
 out=''
 for c in s:
  if width(out+c)>max(0,n-1):break
  out+=c
 return out+'…' if n else ''
def main(screen):
 curses.curs_set(0);curses.start_color();curses.use_default_colors()
 curses.init_pair(1,151,-1);curses.init_pair(2,224,-1)
 screen.timeout(100);curses.mousemask(curses.ALL_MOUSE_EVENTS)
 selected=0;offset=0;rows=[];status={};last=0;previous=None
 while True:
  if time.monotonic()-last>.5:
   try:
    status=values(request('status'));rows=[]
    for line in request('playlistinfo'):
     if line.startswith('file: '):rows.append({'file':line[6:]})
     elif rows and ': ' in line:
      key,value=line.split(': ',1);rows[-1][key]=value
    song=status.get('songid')
    if song!=previous:
     selected=next((i for i,row in enumerate(rows) if row.get('Id')==song),selected);previous=song
   except (OSError,RuntimeError):status={}
   last=time.monotonic()
  h,w=screen.getmaxyx();height=max(1,h-1);selected=max(0,min(selected,len(rows)-1))
  offset=max(0,min(offset,max(0,len(rows)-height)))
  if selected<offset:offset=selected
  if selected>=offset+height:offset=selected-height+1
  screen.erase()
  for y,row in enumerate(rows[offset:offset+height]):
   title=row.get('Title') or os.path.splitext(os.path.basename(row['file']))[0]
   text=(row.get('Artist','')+' '+title).strip()
   secs=int(float(row.get('duration',row.get('Time','0'))));duration=f'{secs//60}:{secs%60:02}'
   dw=max(5,len(duration));limit=max(0,w-dw-2)
   playing=row.get('Id')==status.get('songid') and status.get('state') in ('play','pause')
   attr=(curses.color_pair(1)|curses.A_BOLD) if playing else curses.A_NORMAL
   if offset+y==selected and not playing:attr|=curses.A_BOLD
   try:
    screen.addstr(y,0,shorten(text,limit),attr)
    screen.addstr(y,w-dw,duration.rjust(dw),attr)
   except curses.error:pass
  if h>1:
   elapsed=float(status.get('elapsed','0'));duration=float(status.get('duration','0'))
   filled=min(w,int(w*elapsed/duration)) if duration else 0
   try:screen.addstr(h-1,0,'━'*filled,curses.color_pair(2))
   except curses.error:pass
  screen.refresh();key=screen.getch()
  try:
   if key in (ord('q'),27):return
   elif key in (ord('j'),curses.KEY_DOWN):selected+=1
   elif key in (ord('k'),curses.KEY_UP):selected-=1
   elif key in (10,13,curses.KEY_ENTER) and rows:request('playid '+rows[selected]['Id'])
   elif key==ord(' '):request('pause 1' if status.get('state')=='play' else 'play')
   elif key in (ord('t'),curses.KEY_HOME):selected=next((i for i,r in enumerate(rows) if r.get('Id')==status.get('songid')),0)
   elif key==curses.KEY_END:selected=len(rows)-1
   elif key in (curses.KEY_NPAGE,ord('G')):selected+=height
   elif key in (curses.KEY_PPAGE,ord('g')):selected-=height
   elif key==ord('u'):request('update')
   elif key==ord('d') and rows:request('deleteid '+rows[selected]['Id'])
   elif key in (ord('1'),ord('2'),9,ord('L')):
    curses.endwin();os.execl('/usr/bin/ncmpcpp','ncmpcpp','-c','@HOME@/.config/ncmpcpp/widget-playlist.conf','-s','browser' if key==ord('2') else 'lyrics' if key==ord('L') else 'playlist')
   elif key==curses.KEY_MOUSE:
    _,mx,my,_,buttons=curses.getmouse()
    if buttons&curses.BUTTON4_PRESSED:selected-=3
    elif hasattr(curses,'BUTTON5_PRESSED') and buttons&curses.BUTTON5_PRESSED:selected+=3
    elif my<height:
     selected=min(offset+my,len(rows)-1)
     if buttons&curses.BUTTON1_DOUBLE_CLICKED and rows:request('playid '+rows[selected]['Id'])
   if key!=-1:last=0
  except (OSError,RuntimeError,curses.error,IndexError):pass
if __name__=='__main__':curses.wrapper(main)
