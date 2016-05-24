#!/usr/bin/env python

import datetime
import gi

gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
import time

loop = GObject.MainLoop()
context = loop.get_context()
GObject.threads_init()
Gst.init(None)

gst_cmd = ' ! '.join([
    'videotestsrc pattern={}',
    'video/x-raw,width=1280,height=720',
    'textoverlay name=overlay ypad=0 font-desc="LiberationSerif 32px" shaded-background=false draw-shadow=false valignment=top halignment=right text=""',
    'autovideosink'
])

pipelines, overlays = [], []
for pattern in ['ball', 'snow']:
    pipelines.append(Gst.parse_launch(gst_cmd.format(pattern)))

for pipeline in pipelines:
    pipeline.set_state(Gst.State.PLAYING)
    overlays.append(pipeline.get_by_name('overlay'))

time.sleep(3)
while 1:
    time.sleep(1)
    title = str(datetime.datetime.now())
    for overlay in overlays:
        overlay.set_property('text', '<span foreground="white" background="blue">' + title + '</span>')
    for pipeline in pipelines:
        pipeline.set_state(Gst.State.PLAYING)

