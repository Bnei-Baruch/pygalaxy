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


#global pipeline
#global f
#f = "ffff"
#global overlay
#loop = GObject.MainLoop()
#context = loop.get_context()
#GObject.threads_init()
Gst.init(None)
#pipeline = None
#pipeline = Gst.parse_launch('filesrc location=/home/yosef/Downloads/SampleVideo_360x240_1mb.mp4 !  decodebin ! textoverlay name=overlay text="ggg" ! videoconvert ! autovideosink')
#pipeline = Gst.parse_launch('udpsrc port=5024 timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" ! rtpjitterbuffer ! rtpvp8depay ! vp8dec ! queue ! videoconvert ! videoscale add-borders=false ! videorate ! textoverlay name=overlay text="ggg" ! ximagesink')
#pipeline = Gst.parse_launch('v4l2srs ! video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 ! vp8enc end-usage=cbr cpu-used=15 deadline=1 target-bitrate=600000 max-intra-bitrate=600000 threads=4 error-resilient=0x00000001 ! rtpvp8pay ! udpsink host=127.0.0.1 port=5004')
#pipeline = Gst.parse_launch('udpsrc timeout=1000000000 port=8004 caps="application/x-rtp, media=video, payload=96, clock-rate=90000, encoding-name=VP8" ! rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true ! rtpvp8depay ! vp8dec ! queue ! videoconvert ! videoscale add-borders=false method=4 ! videorate ! interlace field-pattern=2:2 ! video/x-raw, format=UYVY, width=720, height=576, framerate=25/1, interlace-mode=interleaved, pixel-aspect-ratio=12/11, colorimetry=bt601, chroma-site=mpeg2 ! textoverlay name=tittle1 ypad=10 xpad=10 font-desc="LiberationSerif 35px" draw-shadow=false shaded-background=false valignment=top halignment=right text=" " ! textoverlay name=tittle2 ypad=10 xpad=360 font-desc="LiberationSerif 35px" draw-shadow=false shaded-background=false valignment=top halignment=right text=" " ! textoverlay name=tittle3 ypad=280 xpad=360 font-desc="LiberationSerif 35px" draw-shadow=false shaded-background=false valignment=top halignment=right text=" " ! textoverlay name=tittle4 ypad=280 xpad=10 font-desc="LiberationSerif 35px" draw-shadow=false shaded-background=false valignment=top halignment=right text=" " ! compositor name=mix timeout=100000000 ! decklinkvideosink device-number=3 mode=3')
#pipeline = Gst.parse_launch('udpsrc timeout=1000000000 port=8004 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" ! rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true ! rtpvp8depay ! vp8dec ! queue ! videoconvert ! videoscale add-borders=false method=4 ! videorate ! interlace field-pattern=2:2 ! video/x-raw, format=UYVY, width=720, height=576, framerate=25/1, interlace-mode=interleaved, pixel-aspect-ratio=12/11, colorimetry=bt601, chroma-site=mpeg2 ! textoverlay name=overlay ypad=0 font-desc="LiberationSerif 65px" shaded-background=false draw-shadow=false valignment=top halignment=right text=" " ! compositor name=mix timeout=100000000 ! decklinkvideosink device-number=4 mode=3')
'''pipeline = Gst.parse_launch(''
udpsrc timeout=1000000000 port=8004 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" ! 
rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true ! 
rtpvp8depay ! 
vp8dec ! 
queue ! 
videoconvert ! 
videoscale add-borders=false method=4 ! 
videorate ! 
textoverlay name=overlay ypad=0 font-desc="LiberationSerif 45px" shaded-background=false draw-shadow=false valignment=top halignment=right text="" ! 
textoverlay name=overlay2 ypad=0 font-desc="LiberationSerif 45px" shaded-background=false draw-shadow=false valignment=top halignment=left text="" ! 
textoverlay name=overlay3 ypad=0 font-desc="LiberationSerif 45px" shaded-background=false draw-shadow=false valignment=bottom halignment=right text="" ! 
textoverlay name=overlay4 ypad=0 font-desc="LiberationSerif 45px" shaded-background=false draw-shadow=false valignment=bottom halignment=left text="" ! 
compositor name=mix timeout=100000000 ! ximagesink'')'''
pipeline = Gst.parse_launch('''
compositor name=mix timeout=100000000 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=0 sink_1::ypos=180 sink_2::xpos=320 sink_2::ypos=0 sink_3::xpos=320 sink_3::ypos=180 sync=false ! 
video/x-raw, format=UYVY, width=640, height=360, framerate=25/1 ! 
videoscale ! 
videorate ! 
videoconvert ! 
vp8enc end-usage=cbr cpu-used=15 deadline=1 target-bitrate=600000 max-intra-bitrate=600000 threads=4 error-resilient=0x00000001 ! 
rtpvp8pay !
queue ! 
tee name=t ! queue ! udpsink host=62.219.8.116 port=8024 t. ! queue ! udpsink host=127.0.0.1 port=8024 t. ! queue ! udpsink host=jnseur.kbb1.com port=8024 \

udpsrc port=5024 name="udpsrc5024" timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" ! rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true ! rtpvp8depay ! queue ! vp8dec ! \
videoscale ! videorate ! videoconvert ! video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 ! mix. \

udpsrc port=5026 name="udpsrc5026" timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" ! rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true ! rtpvp8depay ! queue ! vp8dec ! \
videoscale ! videorate ! videoconvert ! video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 ! mix. \

udpsrc port=5028 name="udpsrc5028" timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" ! rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true ! rtpvp8depay ! queue ! vp8dec ! \
videoscale ! videorate ! videoconvert ! video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 ! mix. \

udpsrc port=5030 name="udpsrc5030" timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" ! rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true ! rtpvp8depay ! queue ! vp8dec ! \
videoscale ! videorate ! videoconvert ! video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 ! mix.
''')


'''

vp8enc end-usage=cbr cpu-used=15 deadline=1 target-bitrate=600000 max-intra-bitrate=600000 threads=4 error-resilient=0x00000001 ! 
rtpvp8pay !
queue ! 
udpsink host=v4g.kbb1.com port=20034 \
'''


pipeline.set_state(Gst.State.PLAYING)
sleep(3)
bus = pipeline.get_bus()

#udpsrc1 = pipeline.get_by_name('udpsrc6030')
#bus1 = udpsrc1.get_bus()
#print bus1
tt_last_timeout=0
start_after_timeout = 0
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
                print tt_log()+" [main loop] Element", ggg.src.get_name()," Message: ", name33
                start_after_timeout = 1
                #pipeline.set_state(Gst.State.READY)
                #pipeline.set_state(Gst.State.PAUSED)
                #pipeline.set_state(Gst.State.PLAYING)
                print tt_log()+" [main loop] Restarting when timeouts starts"

            #print ggg.src.get_state()
    except:
        pass#print "NO MESSAGES"
    if start_after_timeout and time()-tt_last_timeout>10:
        print tt_log()+" [main loop] Restarting after timeouts"
        pipeline.set_state(Gst.State.READY)
        pipeline.set_state(Gst.State.PAUSED)
        pipeline.set_state(Gst.State.PLAYING)
        start_after_timeout = 0
    #sleep(1)

