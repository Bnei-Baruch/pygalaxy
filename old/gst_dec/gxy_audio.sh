while :
do

/usr/local/bin/gst-launch-1.0 \
udpsrc port=8042 caps="application/x-rtp, media=audio, payload=111, clock-rate=48000, encoding-name=X-GST-OPUS-DRAFT-SPITTKA-00" ! \
rtpopusdepay ! opusdec plc=true ! audioconvert ! \
alsasink

done
