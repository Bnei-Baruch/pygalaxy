#!/usr/bin/env python
from multiprocessing import Process, Queue
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from time import sleep,time,localtime
from socket import socket

import sys
import os

script_name = os.path.basename(__file__)
script_name = script_name.split(".")[0]

log_path = 'logs' 
if not os.path.exists(log_path):
    os.makedirs(log_path)

def first_zero(num,cnt=2):
    num = str(num)
    while len(num)<cnt:
        num = '0'+num
    return num

def tt_log():
    ttuple = localtime(time())
    return str(ttuple.tm_year)+first_zero(ttuple.tm_mon)+first_zero(ttuple.tm_mday)+"_"+first_zero(ttuple.tm_hour)+":"+first_zero(ttuple.tm_min)+":"+first_zero(ttuple.tm_sec)

sys.stdout = open(log_path+"/"+script_name+"_"+tt_log()+".log","w",0)



global pipeline
global f
f = "ffff"
global overlay
loop = GObject.MainLoop()
context = loop.get_context()
GObject.threads_init()
Gst.init(None)
pipeline = None

#udpsrc port=8024 caps="application/x-rtp, media=video, payload=96, clock-rate=90000, encoding-name=VP8" ! rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true ! rtpvp8depay ! vp8dec ! queue ! videoconvert ! videoscale add-borders=false method=4 ! videorate ! interlace field-pattern=2:2 ! video/x-raw, format=UYVY, width=720, height=576, framerate=25/1, interlace-mode=interleaved, pixel-aspect-ratio=12/11, colorimetry=bt601, chroma-site=mpeg2 ! textoverlay name=tittle1 ypad=10 xpad=10 font-desc="LiberationSerif 35px" draw-shadow=false shaded-background=false valignment=top halignment=right text=" " ! textoverlay name=tittle2 ypad=10 xpad=360 font-desc="LiberationSerif 35px" draw-shadow=false shaded-background=false valignment=top halignment=right text=" " ! textoverlay name=tittle3 ypad=280 xpad=360 font-desc="LiberationSerif 35px" draw-shadow=false shaded-background=false valignment=top halignment=right text=" " ! textoverlay name=tittle4 ypad=280 xpad=10 font-desc="LiberationSerif 35px" draw-shadow=false shaded-background=false valignment=top halignment=right text=" " ! compositor name=mix timeout=100000000 ! decklinkvideosink device-number=2 mode=3

pipeline = Gst.parse_launch('''
udpsrc timeout=1000000000 port=8024 caps="application/x-rtp, media=video, payload=96, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" ! 
rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true ! 
rtpvp8depay ! 
vp8dec ! 
queue ! 
videoconvert ! 
videoscale add-borders=false method=4 ! 
videorate ! 
interlace field-pattern=2:2 !
video/x-raw, format=UYVY, width=720, height=576, framerate=25/1, interlace-mode=interleaved, pixel-aspect-ratio=12/11, colorimetry=bt601, chroma-site=mpeg2 !
textoverlay name=tittle1 ypad=10 xpad=10 font-desc="LiberationSerif 35px" draw-shadow=false shaded-background=false valignment=top halignment=right text="" !
textoverlay name=tittle2 ypad=10 xpad=360 font-desc="LiberationSerif 35px" draw-shadow=false shaded-background=false valignment=top halignment=right text="" !
textoverlay name=tittle3 ypad=280 xpad=360 font-desc="LiberationSerif 35px" draw-shadow=false shaded-background=false valignment=top halignment=right text="" !
textoverlay name=tittle4 ypad=280 xpad=10 font-desc="LiberationSerif 35px" draw-shadow=false shaded-background=false valignment=top halignment=right text="" !
compositor name=mix timeout=100000000 !
decklinkvideosink device-number=2 mode=3''')
pipeline.set_state(Gst.State.PLAYING)
sleep(3)
bus = pipeline.get_bus()
#bus.add_signal_watch()
overlay_dict = {}
#overlay_dict['8004'] = pipeline.get_by_name('overlay')
overlay_dict['5024'] = pipeline.get_by_name('tittle2')
overlay_dict['5026'] = pipeline.get_by_name('tittle3')
overlay_dict['5028'] = pipeline.get_by_name('tittle1')
overlay_dict['5030'] = pipeline.get_by_name('tittle4')
global q
q = Queue()



def recieve_title_from_socket():
    host = 'localhost'
    port = 9090
    client_id = '5024,5026,5028,5030'#'8004'
    global q
    while 1:
        try:
            sock = socket()
            sock.connect((host,port))
            sock.send(client_id+'#')
            print tt_log()+" [recieve_title_from_socket] socket connected"
            break
        except:
            print tt_log()+" [recieve_title_from_socket] socket not connected"
            sleep(3)
            
    while 1:
        print tt_log()+" [recieve_title_from_socket] start cycle"
        rcv = sock.recv(1024)
        if rcv == '':
           while 1:
               print tt_log()+' [recieve_title_from_socket] socket try reconnect'
               try:
                   sock = socket()
                   sock.connect((host,port))
                   sock.send(client_id+'#')
                   print tt_log()+' [recieve_title_from_socket] socket reconnected'
                   break
               except:
                   print tt_log()+" [recieve_title_from_socket] can not reconnect" 
               sleep(3)
           
        else:
            print tt_log()+" [recieve_title] recieved: "+rcv

            while rcv.count("#")>1:
                rcv = rcv[rcv.find("#")+1:]
            title = rcv[:rcv.find("#")]
            q.put(title)
            
            print tt_log()+" [recieve_title] New title puted in Q: "+title
    
l = Process(target=recieve_title_from_socket)
l.start()   

#noStream = 2
start_after_timeout = 0
### main loop
while 1:
    sleep(0.01)
    try:
        ggg = bus.poll(Gst.MessageType.ELEMENT,10) #type Gst.Message
        #print "SOURCE: ",ggg.src
        #print ggg
        struct = ggg.get_structure()
        name33 = struct.get_name()
        if (name33 == 'GstUDPSrcTimeout'):# or name33 == 'GstMessageQOS'):
            #print "SOURCE: ",ggg.src.get_name() # type Gst.Element
            #print "TYPE: ", ggg.type
            tt_last_timeout = time()
            if start_after_timeout==0:
                print tt_log()+" [main loop] Element: ", ggg.src.get_name(),", Message: ", name33
                start_after_timeout = 1
                pipeline.set_state(Gst.State.READY)
                pipeline.set_state(Gst.State.PAUSED)
                pipeline.set_state(Gst.State.PLAYING)
                print tt_log()+" [main loop] Restarting when timeouts starts"

            #print ggg.src.get_state()
    except:
        pass#print "NO MESSAGES"
    if start_after_timeout and time()-tt_last_timeout>3:
        print tt_log()+" [main loop] Restarting after timeouts"
        pipeline.set_state(Gst.State.READY)
        pipeline.set_state(Gst.State.PAUSED)
        pipeline.set_state(Gst.State.PLAYING)
        start_after_timeout = 0
    message = ''
    try:
        message=q.get(False)
        print tt_log()+" [main loop] recieved new message: "+message
    except:
        pass
    if message!='':
        port = message[:message.find(':')]
        title = message[message.find(':')+1:]
        if overlay_dict.has_key(port):
            overlay_dict[port].set_property('text', '<span foreground="white" background="blue">'+title+'</span>')
            pipeline.set_state(Gst.State.PLAYING)
        print tt_log()+' [main loop] updated new title: '+ message

        
