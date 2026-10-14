#!/usr/bin/python3
import os,subprocess,signal,math
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,Gdk,GLib
import cairo
ROOT='@HOME@/.config/ncmpcpp/'
class Spectrum(Gtk.Window):
 def __init__(self):
  super().__init__(title='MusicWidgetSpectrum')
  self.set_wmclass('MusicWidgetSpectrum','MusicWidgetSpectrum')
  self.set_decorated(False);self.set_keep_above(True);self.set_skip_taskbar_hint(True)
  self.set_default_size(182,164);self.set_app_paintable(True)
  vis=self.get_screen().get_rgba_visual()
  if vis:self.set_visual(vis)
  self.connect('draw',self.draw);self.connect('destroy',self.close)
  self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
  self.connect('button-press-event',self.drag)
  env=os.environ.copy();env.pop('LD_LIBRARY_PATH',None)
  self.proc=subprocess.Popen(['/usr/bin/cava','-p',ROOT+'cava-lines.conf'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env)
  os.set_blocking(self.proc.stdout.fileno(),False)
  self.buf=b'';self.values=[0.0]*30;self.target=[0.0]*30
  GLib.timeout_add(16,self.tick)
 def drag(self,widget,event):
  if event.button==1:self.begin_move_drag(event.button,int(event.x_root),int(event.y_root),event.time)
 def tick(self):
  try:
   while True:
    data=os.read(self.proc.stdout.fileno(),4096)
    if not data:break
    self.buf+=data
  except BlockingIOError:pass
  frames=len(self.buf)//30
  if frames:
   frame=self.buf[(frames-1)*30:frames*30];self.buf=self.buf[frames*30:]
   self.target=[v/255 for v in frame]
  for i,v in enumerate(self.target):
   factor=.62 if v>self.values[i] else .19
   self.values[i]+=(v-self.values[i])*factor
  self.queue_draw();return True
 def draw(self,widget,c):
  w,h=self.get_allocated_width(),self.get_allocated_height()
  c.set_operator(cairo.OPERATOR_SOURCE);c.set_source_rgba(0,0,0,0);c.paint();c.set_operator(cairo.OPERATOR_OVER)
  r=10
  for cx,cy,a in [(w-r,r,-math.pi/2),(w-r,h-r,0),(r,h-r,math.pi/2),(r,r,math.pi)]:c.arc(cx,cy,r,a,a+math.pi/2)
  c.close_path();c.set_source_rgba(105/255,66/255,82/255,.20);c.fill()
  left,right,base=9,w-9,h-11
  c.set_line_cap(cairo.LINE_CAP_ROUND)
  # Fine baseline and soft halos, with no particles or background changes.
  for width,alpha in [(5,.045),(2.5,.12),(1,.8)]:
   c.set_source_rgba(1,.77,.88,alpha);c.set_line_width(width);c.move_to(left,base);c.line_to(right,base);c.stroke()
  for i,v in enumerate(self.values):
   x=left+(right-left)*i/29
   height=max(1.3,min(.90,v**1.15)*(h-30))
   for width,alpha in [(7.5,.05),(5.5,.14),(3.8,.96)]:
    c.set_source_rgba(1,.72+.20*v,.86+.10*v,alpha);c.set_line_width(width)
    c.move_to(x,base-1);c.line_to(x,base-height);c.stroke()
  return False
 def close(self,*args):
  self.proc.terminate();Gtk.main_quit()
win=Spectrum();win.show_all()
signal.signal(signal.SIGTERM,lambda *args:win.destroy())
Gtk.main()
