#!/usr/bin/env python
import gi

gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from time import sleep, time, localtime

import sys
import os

script_name = os.path.basename(__file__)
script_name = script_name.split(".")[0]

log_path = 'logs'
if not os.path.exists(log_path):
    os.makedirs(log_path)


def first_zero(num, cnt=2):
    num = str(num)
    while len(num) < cnt:
        num = '0' + num
    return num


def tt_log():
    ttuple = localtime(time())
    return str(ttuple.tm_year) + first_zero(ttuple.tm_mon) + first_zero(ttuple.tm_mday) + "_" + first_zero(
        ttuple.tm_hour) + ":" + first_zero(ttuple.tm_min) + ":" + first_zero(ttuple.tm_sec)

sys.stdout = open(log_path + "/" + script_name + "_" + tt_log() + ".log", "w", 0)

Gst.init(None)
pipeline = Gst.parse_launch('''
compositor name=mix timeout=100000000 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=0 sink_1::ypos=180 sink_2::xpos=320 sink_2::ypos=0 sink_3::xpos=320 sink_3::ypos=180 sync=false ! 
video/x-raw, format=UYVY, width=640, height=360, framerate=25/1 ! 
videoscale ! 
videorate ! 
videoconvert ! 
vp8enc end-usage=cbr cpu-used=15 deadline=1 target-bitrate=600000 max-intra-bitrate=600000 threads=4 error-resilient=0x00000001 ! 
rtpvp8pay !
queue ! 
tee name=t ! queue ! udpsink host=jnseur.kbb1.com port=20024 t. ! queue ! udpsink host=127.0.0.1 port=20024 \

udpsrc port=6024 name="udpsrc6024" timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" ! rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true ! rtpvp8depay ! queue ! vp8dec ! \
videoscale ! videorate ! videoconvert ! video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 ! mix. \

udpsrc port=6026 name="udpsrc6026" timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" ! rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true ! rtpvp8depay ! queue ! vp8dec ! \
videoscale ! videorate ! videoconvert ! video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 ! mix. \

udpsrc port=6028 name="udpsrc6028" timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" ! rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true ! rtpvp8depay ! queue ! vp8dec ! \
videoscale ! videorate ! videoconvert ! video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 ! mix. \

udpsrc port=6030 name="udpsrc6030" timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" ! rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true ! rtpvp8depay ! queue ! vp8dec ! \
videoscale ! videorate ! videoconvert ! video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 ! mix.
''')

pipeline.set_state(Gst.State.PLAYING)
sleep(3)
bus = pipeline.get_bus()

tt_last_timeout = 0
start_after_timeout = 0
while 1:
    sleep(0.01)
    try:
        ggg = bus.poll(Gst.MessageType.ELEMENT, 10)  # type Gst.Message
        struct = ggg.get_structure()
        name33 = struct.get_name()
        if name33 == 'GstUDPSrcTimeout':  # or name33 == 'GstMessageQOS':
            tt_last_timeout = time()
            if start_after_timeout == 0:
                print tt_log() + " [main loop] Element", ggg.src.get_name(), " Message: ", name33
                start_after_timeout = 1
                print tt_log() + " [main loop] Restarting when timeouts starts"
    except:
        pass  # no messages
    if start_after_timeout and time() - tt_last_timeout > 10:
        print tt_log() + " [main loop] Restarting after timeouts"
        pipeline.set_state(Gst.State.READY)
        pipeline.set_state(Gst.State.PAUSED)
        pipeline.set_state(Gst.State.PLAYING)
        start_after_timeout = 0
