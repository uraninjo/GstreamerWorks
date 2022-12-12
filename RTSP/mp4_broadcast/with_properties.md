gst-launch-1.0 filesrc location='/opt/nvidia/deepstream/deepstream-6.1/samples/streams/sample_720p.mp4' ! qtdemux ! avdec_h264 direct-rendering=true lowres=0 max-threads=0 output-corrupt=false skip-frame=0 ! videoconvert ! x264enc aud=true b-adapt=true b-pyramid=false bframes=0 bitrate=2048 byte-stream=false cabac=true dct8x8=false ip-factor=1.4 key-int-max=0 noise-reduction=0 qp-max=51 qp-min=10 qp-step=4 quantizer=21 rc-lookahead=40 sliced-threads=true tune=zerolatency speed-preset=6 ! rtspclientsink location=rtsp://127.0.0.1:8554/test latency=1000


gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/test latency=1000 ! rtph264depay ! avdec_h264 direct-rendering=true lowres=0 max-threads=0 output-corrupt=false skip-frame=0 ! xvimagesink



