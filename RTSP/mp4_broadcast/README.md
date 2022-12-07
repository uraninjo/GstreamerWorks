### Sender: 
gst-launch-1.0 -v filesrc location = /opt/nvidia/deepstream/deepstream-6.1/samples/streams/sample_720p.mp4 ! decodebin ! autovideoconvert ! x264enc ! rtspclientsink location=rtsp://127.0.0.1:8554/test 

#### Custom Decoder:

gst-launch-1.0 -v filesrc location = /opt/nvidia/deepstream/deepstream-6.1/samples/streams/sample_720p.mp4 ! qtdemux ! avdec_h264 ! videoconvert ! x264enc ! rtspclientsink location=rtsp://127.0.0.1:8554/test 

### Recievers: 
gst-launch-1.0 -v rtspsrc location=rtsp://127.0.0.1:8554/test  caps="application/x-rtp,media=video,clock-rate=90000,payload=96" ! rtph264depay ! avdec_h264 ! decodebin ! videoconvert ! xvimagesink 
 
gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/test caps="application/x-rtp,media=video,clock-rate=90000,payload=96" ! rtph264depay ! avdec_h264 ! autovideosink 

gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/test ! rtph264depay ! avdec_h264 ! xvimagesink 



### Nvidia
gst-launch-1.0 filesrc location='samples/streams/sample_720p.mp4' ! nvv4l2decoder ! nvvideoconvert ! nvv4l2h264enc ! rtspclientsink location=rtsp://127.0.0.1:8554/test

gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/test ! rtph264depay ! nvv4l2decoder ! xvimagesink

### CPU
gst-launch-1.0 filesrc location='ElephantsDream.mp4' ! qtdemux ! avdec_h264 ! videoconvert ! x264enc ! rtspclientsink location=rtsp://127.0.0.1:8554/test

gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/test ! rtph264depay ! avdec_h264 ! xvimagesink	
