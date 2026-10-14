#!/usr/bin/python3
import ctypes as C, math, subprocess, sys
x11=C.CDLL('libX11.so.6'); ext=C.CDLL('libXext.so.6')
x11.XOpenDisplay.argtypes=[C.c_char_p];x11.XOpenDisplay.restype=C.c_void_p
x11.XCloseDisplay.argtypes=[C.c_void_p]
x11.XFlush.argtypes=[C.c_void_p]
class Rect(C.Structure):
 _fields_=[('x',C.c_short),('y',C.c_short),('width',C.c_ushort),('height',C.c_ushort)]
ext.XShapeCombineRectangles.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_int,C.c_int,C.POINTER(Rect),C.c_int,C.c_int,C.c_int]
win=int(sys.argv[1]); vals=dict(line.split('=',1) for line in subprocess.check_output(['xdotool','getwindowgeometry','--shell',str(win)],text=True).splitlines())
w,h=int(vals['WIDTH']),int(vals['HEIGHT']);r=10
rows=[]
for y in range(h):
 dy=max(r-y-.5,y+.5-(h-r),0)
 inset=math.ceil(r-math.sqrt(max(0,r*r-dy*dy))) if dy else 0
 rows.append(Rect(inset,y,w-2*inset,1))
d=x11.XOpenDisplay(None)
if not d:sys.exit(1)
ext.XShapeCombineRectangles(d,win,0,0,0,(Rect*len(rows))(*rows),len(rows),0,0)
x11.XFlush(d);x11.XCloseDisplay(d)
