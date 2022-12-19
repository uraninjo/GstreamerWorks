### Sender: 
gst-launch-1.0 -v filesrc location = /opt/nvidia/deepstream/deepstream-6.1/samples/streams/sample_720p.mp4 ! decodebin ! autovideoconvert ! x264enc ! rtspclientsink location=rtsp://127.0.0.1:8554/test 

#### Custom Decoder:

gst-launch-1.0 -v filesrc location = /opt/nvidia/deepstream/deepstream-6.1/samples/streams/sample_720p.mp4 ! qtdemux ! avdec_h264 ! videoconvert ! x264enc ! rtspclientsink location=rtsp://127.0.0.1:8554/test 

### Recievers: 
gst-launch-1.0 -v rtspsrc location=rtsp://127.0.0.1:8554/test  caps="application/x-rtp,media=video,clock-rate=90000,payload=96" ! rtph264depay ! avdec_h264 ! decodebin ! videoconvert ! xvimagesink 
 
gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/test caps="application/x-rtp,media=video,clock-rate=90000,payload=96" ! rtph264depay ! avdec_h264 ! autovideosink 

gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/test ! rtph264depay ! avdec_h264 ! xvimagesink 



### Nvidia
gst-launch-1.0 filesrc location='/opt/nvidia/deepstream/deepstream-6.1/samples/streams/sample_720p.mp4' ! qtdemux ! h264parse ! nvv4l2decoder ! nvvideoconvert ! nvv4l2h264enc ! rtspclientsink location=rtsp://127.0.0.1:8554/test


gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/test ! rtph264depay ! nvv4l2decoder ! nvvideoconvert  ! nveglglessink


gst-launch-1.0 filesrc location='/opt/nvidia/deepstream/deepstream-6.1/samples/streams/sample_720p.mp4' ! qtdemux ! h264parse ! nvv4l2decoder capture-io-mode=auto cudadec-memtype=memtype_device drop-frame-interval=0 low-latency-mode=false num-extra-surfaces=0 output-io-mode=mmap skip-frames=0 ! nvvideoconvert ! nvv4l2h264enc bitrate=4000000 capture-io-mode=auto extended-colorformat=true force_idr=false force-intra=false gpu-id=0 iframeinterval=0 output-io-mode=mmap qos=true ! rtspclientsink location=rtsp://127.0.0.1:8554/test

gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/test ! rtph264depay ! nvv4l2decoder capture-io-mode=auto cudadec-memtype=memtype_device drop-frame-interval=0 low-latency-mode=false num-extra-surfaces=0 output-io-mode=mmap skip-frames=0 ! nvvideoconvert  ! nveglglessink


### CPU

gst-launch-1.0 filesrc location='Murat/ElephantsDream.mp4' ! qtdemux ! avdec_h264 ! videoconvert ! x264enc ! rtspclientsink location=rtsp://127.0.0.1:8554/test

gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/test ! rtph264depay ! avdec_h264 ! xvimagesink	

gst-launch-1.0 filesrc location='/opt/nvidia/deepstream/deepstream-6.1/samples/streams/sample_720p.mp4' ! qtdemux ! avdec_h264 direct-rendering=true lowres=0 max-threads=0 output-corrupt=false skip-frame=0 ! videoconvert ! x264enc aud=true b-adapt=true b-pyramid=false bframes=0 bitrate=2048 byte-stream=false cabac=true dct8x8=false ip-factor=1.4 key-int-max=0 noise-reduction=0 qp-max=51 qp-min=10 qp-step=4 quantizer=21 rc-lookahead=40 sliced-threads=true tune=zerolatency speed-preset=6 ! rtspclientsink location=rtsp://127.0.0.1:8554/test latency=1000


gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/test latency=1000 ! rtph264depay ! avdec_h264 direct-rendering=true lowres=0 max-threads=0 output-corrupt=false skip-frame=0 ! xvimagesink


