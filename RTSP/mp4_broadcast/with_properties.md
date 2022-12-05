gst-launch-1.0 -v filesrc location =ElephantsDream.mp4 ! qtdemux ! avdec_h264 ! videoconvert ! x264enc ! rtspclientsink location=rtsp://127.0.0.1:8554/test 

gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/test ! rtph264depay ! avdec_h264 output-corrupt=false debug-mv=true direct-rendering=true lowres=1/4-size skip-frame=5 ! xvimagesink 


