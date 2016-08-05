#!/usr/bin/env bash

gst-launch-1.0 -v \
compositor name=mix timeout=100000000 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=0 sink_1::ypos=180 sink_2::xpos=320 sink_2::ypos=0 sink_3::xpos=320 sink_3::ypos=180 sync=false ! \
textoverlay name=overlay1 ypad=0  xpad=330 text="<span foreground=\"white\" background=\"blue\">SMPTE</span>" font-desc="LiberationSerif 32px" shaded-background=false draw-shadow=false valignment=top halignment=right ! \
textoverlay name=overlay2 ypad=180  xpad=330 text="<span foreground=\"white\" background=\"blue\">snow</span>" font-desc="LiberationSerif 32px" shaded-background=false draw-shadow=false valignment=top halignment=right ! \
textoverlay name=overlay3 ypad=0  xpad=10 text="<span foreground=\"white\" background=\"blue\">spokes</span>" font-desc="LiberationSerif 32px" shaded-background=false draw-shadow=false valignment=top halignment=right ! \
textoverlay name=overlay4 ypad=180  xpad=10 text="<span foreground=\"white\" background=\"blue\">ball</span>" font-desc="LiberationSerif 32px" shaded-background=false draw-shadow=false valignment=top halignment=right ! \
autovideosink \
videotestsrc pattern=0 ! mix. \
videotestsrc pattern=snow ! mix. \
videotestsrc pattern=spokes ! mix. \
videotestsrc pattern=ball ! mix. \



#
#gst-launch-1.0 -v \
# videotestsrc pattern=ball ! \
# video/x-raw,width=400,height=300 ! \
# textoverlay name=overlay text="<span foreground=\"white\" background=\"blue\">edos</span>" ypad=0 font-desc="LiberationSerif 32px" shaded-background=false draw-shadow=false valignment=top halignment=right ! \
# autovideosink



# Stream webcam over udp:
#   http://stackoverflow.com/questions/7669240/webcam-streaming-using-gstreamer-over-udp
# server:
gst-launch-1.0 v4l2src ! x264enc pass=qual quantizer=20 tune=zerolatency ! rtph264pay ! udpsink host=127.0.0.1 port=5030

# client
gst-launch-1.0 udpsrc port=5030 ! "application/x-rtp, payload=127" ! rtph264depay ! avdec_h264 ! xvimagesink sync=false



gst-launch-1.0 videotestsrc pattern=ball ! jpegenc ! rtpjpegpay ! udpsink host=127.0.0.1 port=5028
gst-launch-1.0 udpsrc port=5028 ! "application/x-rtp, encoding-name=JPEG, payload=26" ! rtpjpegdepay ! jpegdec ! autovideosink




gst-launch-1.0 multifilesrc location="IMG_0726.JPG" caps="image/jpeg,framerate=1/1" ! jpegdec ! videoconvert ! videorate ! x264enc pass=qual quantizer=20 tune=zerolatency ! rtph264pay ! udpsink host=127.0.0.1 port=5028