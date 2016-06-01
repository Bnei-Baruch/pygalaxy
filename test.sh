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
