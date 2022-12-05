import sys
import gi
import logging

gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gst, GLib, GObject

uri_name='rtsp://127.0.0.1:8554/test'

def cb_newpad(demux, src, sink):
    print("In cb_newpad\n")
    caps=src.get_current_caps()
    gststruct=caps.get_structure(0)
    gstname=gststruct.get_name()
    features=caps.get_features(0)

    print("gstname=",gstname)
    if(gstname.find("video")!=-1):
        print("features=",features)
        sink_pad=sink.get_static_pad("sink")
        src.link(sink_pad)
        """if not src.link(sink_pad):
            sys.stderr.write("Failed to link decoder src pad to source bin ghost pad\n")"""



logging.basicConfig(level=logging.DEBUG, format="[%(name)s] [%(levelname)8s] - %(message)s")
logger = logging.getLogger(__name__)

Gst.init(None)

pipeline=Gst.Pipeline.new('test-pipeline')

source=Gst.ElementFactory.make('rtspsrc','source')
source.set_property('location', uri_name)

depay=Gst.ElementFactory.make("rtph264depay", "depay")



decoder=Gst.ElementFactory.make('avdec_h264','decoder')
sink=Gst.ElementFactory.make('xvimagesink','sink')

pipeline.add(source)
pipeline.add(depay)

source.connect('pad-added', cb_newpad, depay)

pipeline.add(decoder)
pipeline.add(sink)



if depay.link(decoder):
    logger.info('depay-decoder Bağlandı')
if decoder.link(sink):
    logger.info('decoder-sink Bağlandı')

ret=pipeline.set_state(Gst.State.PLAYING)

if ret==Gst.StateChangeReturn.FAILURE:
    logger.error("pipeline'da sıkıntı var")
    sys.exit(1)

bus = pipeline.get_bus()
msg = bus.timed_pop_filtered(
    Gst.CLOCK_TIME_NONE, 
    Gst.MessageType.ERROR | Gst.MessageType.EOS)

if msg:
    if msg.type == Gst.MessageType.ERROR:
        err, debug_info = msg.parse_error()
        logger.error(f"Error received from element {msg.src.get_name()}: {err.message}")
        logger.error(f"Debugging information: {debug_info if debug_info else 'none'}")

    elif msg.type == Gst.MessageType.EOS:
        logger.info("End-Of-Stream reached.")

    else:
        # This should not happen as we only asked for ERRORs and EOS
        logger.error("Unexpected message received.")

pipeline.set_state(Gst.State.NULL)