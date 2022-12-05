### Sender
gst-launch-1.0 rtspsrc location= ! rtph264depay ! avdec_h264 ! videoconvert ! x264enc ! rtspclientsink location=rtsp://127.0.0.1:8554/test


### Reciever
gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/test ! rtph264depay ! avdec_h264 output-corrupt=false ! xvimagesink

