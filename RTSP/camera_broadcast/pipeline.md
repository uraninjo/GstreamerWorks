### Sender
gst-launch-1.0 -v rtspsrc location = ! decodebin ! autovideoconvert ! x264enc ! rtspclientsink location=rtsp://127.0.0.1:8554/test 

### Reciever
gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/test ! rtph264depay ! avdec_h264 ! autovideosink 
