pkill screen
pkill python

sleep 1

screen -S audio -d -m /opt/gst_dec/gxy_audio.sh

python /opt/gst_dec/gst_socket.py 1> /opt/gst_dec/gst_socket.log 2>&1 &
python /opt/gst_dec/gst_web.py 1> /opt/gst_dec/gst_web.log 2>&1 &
python /opt/gst_dec/gst_sdi1.py 1> /opt/gst_dec/gst_sdi1.log 2>&1 &
python /opt/gst_dec/gst_sdi2.py 1> /opt/gst_dec/gst_sdi2.log 2>&1 &
python /opt/gst_dec/gst_sdi3.py 1> /opt/gst_dec/gst_sdi3.log 2>&1 &
python /opt/gst_dec/gst_sdi5.py 1> /opt/gst_dec/gst_sdi5.log 2>&1 &

