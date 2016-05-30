#!/usr/bin/env python

import datetime
import gi

gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
import time


# loop = GObject.MainLoop()
# context = loop.get_context()

# Initialize thread support in PyGObject
# https://wiki.gnome.org/Projects/PyGObject/Threading
# GObject.threads_init()

# Initialize GStreamer library
# https://gstreamer.freedesktop.org/data/doc/gstreamer/head/gstreamer/html/gstreamer-Gst.html#gst-init
Gst.init(None)

gst_cmd = ' ! '.join([
    'udpsrc port=5004 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01"',
    'rtpjitterbuffer',
    'rtpvp8depay',
    'queue',
    'vp8dec',
    'videoconvert',
    'videoscale add-borders=false method=4',
    'videorate',
    'interlace field-pattern=2:2',
    'video/x-raw, format=UYVY, width=720, height=576, framerate=25/1, interlace-mode=interleaved, pixel-aspect-ratio=12/11, colorimetry=bt601, chroma-site=mpeg2',
    'textoverlay name=overlay ypad=0 font-desc="LiberationSerif 32px" shaded-background=false draw-shadow=false valignment=top halignment=right text=""',
    'decklinkvideosink mode=3'
])


pipeline = Gst.parse_launch(gst_cmd)
pipeline.set_state(Gst.State.PLAYING)
overlay = pipeline.get_by_name('overlay')

# time.sleep(3)
for _ in xrange(5):
    title = str(datetime.datetime.now())
    print 'setting overlay'
    overlay.set_property('text', '<span foreground="white" background="blue">' + title + '</span>')
    # for pipeline in pipelines:
    #     pipeline.set_state(Gst.State.PLAYING)
    time.sleep(1)

pipeline.set_state(Gst.State.NULL)
# pipeline.unref()

