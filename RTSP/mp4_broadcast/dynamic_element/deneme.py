import sys
import gi
import logging
from threading import Thread, Event
gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gst, GLib, GObject
import logging
import datetime
from gi.repository import Gst, GObject

log = logging.getLogger("Pad-Probe")

def logging_pad_probe(pad, probeinfo, location):
    pts_nanpseconds = probeinfo.get_buffer().pts
    pts_timedelta = datetime.timedelta(microseconds=pts_nanpseconds / 1000)
    log.debug("PTS at %s = %s", '{:>20s}'.format(location), pts_timedelta)
    return Gst.PadProbeReturn.OK

log = logging.getLogger('Runner')

class Runner(object):
    def __init__(self, pipeline, error_callback=None):
        self.mainloop = GObject.MainLoop()
        self.pipeline = pipeline
        self.error_callback = error_callback or self.quit

    def run_blocking(self):
        self.configure()
        self.set_playing()

        try:
            self.mainloop.run()
        except KeyboardInterrupt:
            print('Terminated via Ctrl-C')

        self.set_null()

    def configure(self):
        log.debug('configuring pipeline')
        bus = self.pipeline.bus

        bus.add_signal_watch()
        bus.connect("message::eos", self.on_eos)
        bus.connect("message::error", self.on_error)
        bus.connect("message::state-changed", self.on_state_change)

    def on_eos(self, _bus, message):
        log.error("EOS from %s (at %s)",
                  message.src.name, message.src.get_path_string())
        self.error_callback()

    def on_error(self, _bus, message):
        (error, debug) = message.parse_error()
        log.error("Error from %s (at %s)\n%s (%s)",
                  message.src.name, message.src.get_path_string(), error, debug)
        self.error_callback()

    def quit(self):
        log.warning('quitting mainloop')
        self.mainloop.quit()

    def on_state_change(self, _bus, message):
        old_state, new_state, pending = message.parse_state_changed()
        if message.src == self.pipeline:
            log.info("Pipeline: State-Change from %s to %s; pending %s",
                     old_state.value_name, new_state.value_name, pending.value_name)
        else:
            log.debug("%s: State-Change from %s to %s; pending %s",
                      message.src.name, old_state.value_name, new_state.value_name, pending.value_name)

    def set_playing(self):
        log.info('requesting state-change to PLAYING')
        self.pipeline.set_state(Gst.State.PLAYING)

    def set_null(self):
        log.info('requesting state-change to NULL')
        self.pipeline.set_state(Gst.State.NULL)
        
file='/home/fkurt/Murat/ElephantsDream.mp4'
file2='/home/fkurt/Murat/video.mp4'

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
        if not src.link(sink_pad):
            sys.stderr.write("Failed to link decoder src pad to source bin ghost pad\n")


logging.basicConfig(level=logging.DEBUG, format="[%(name)s] [%(levelname)8s] - %(message)s")
logger = logging.getLogger(__name__)

Gst.init(None)


pipeline=Gst.Pipeline.new('test-pipeline')

source=Gst.ElementFactory.make('filesrc','source')
source.set_property('location', file)

demux=Gst.ElementFactory.make("qtdemux", "demux")
if not demux:
    sys.stderr.write(" Unable to create demux \n")
decoder=Gst.ElementFactory.make('avdec_h264','decoder')
demux.connect("pad-added", cb_newpad, decoder)


caps=Gst.caps_from_string("video/x-raw, width=1280, height=720, framerate=(fraction)24/1")


filter=Gst.ElementFactory.make('capsfilter','filter')

videoconvert=Gst.ElementFactory.make('videoconvert','convert')


sink=Gst.ElementFactory.make('xvimagesink','sink')
if not sink:
    sys.stderr.write(" Unable to create udpsink")

if not sink or not decoder or not videoconvert or not pipeline:
    logger.error('Elementlerde sıkıntı var...')
    sys.exit(1)

pipeline.add(source)
pipeline.add(demux)
pipeline.add(decoder)
pipeline.add(filter)
pipeline.add(videoconvert)

pipeline.add(sink)

if source.link(demux):
    logger.info('src-demux Bağlandı')


if decoder.link(filter):
    logger.info('decoder-videoconvert Bağlandı')

if filter.link(videoconvert):
    logger.info('decoder-videoconvert Bağlandı')
    
if videoconvert.link(sink):
    logger.info('videoconvert-x264enc Bağlandı')

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

def add_new_src():
    global testsrc2, capsfilter2, mixerpad
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "adding-testsrc2-before")
    log.info("Adding testsrc2")

    log.info("Creating testsrc2")
    testsrc2=Gst.ElementFactory.make('filesrc','source')
    testsrc2.set_property('location', file2)

    testsrc2.get_static_pad("src").add_probe(
        Gst.PadProbeType.BUFFER, logging_pad_probe, "testsrc2-output")

    log.info("Adding testsrc2")
    log.debug(pipeline.add(testsrc2))

    log.info("Creating capsfilter")
    capsfilter2 = Gst.ElementFactory.make("capsfilter", "capsfilter2")  # (3)
    capsfilter2.set_property("caps", caps)

    log.info("Adding capsfilter")
    log.debug(pipeline.add(capsfilter2))

    log.info("Linking testsrc2 to capsfilter2")
    log.debug(testsrc2.link(capsfilter2))

    log.info("Syncing Element-States with Pipeline")
    log.debug(capsfilter2.sync_state_with_parent())
    log.debug(testsrc2.sync_state_with_parent())

    log.info("Adding testsrc2 done")
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "adding-testsrc2-after")  # (4)


def remove_src():
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "removing-testsrc2-before")
    log.info("Removing testsrc2")

    log.info("Stopping testsrc2")
    log.debug(testsrc2.set_state(Gst.State.NULL))  # (5)

    log.info("Stopping capsfilter2")
    log.debug(capsfilter2.set_state(Gst.State.NULL))

    log.info("Removing testsrc2")
    log.debug(pipeline.remove(testsrc2))

    log.info("Removing capsfilter2")
    log.debug(pipeline.remove(capsfilter2))

    log.info("Removing testsrc2 done")
    Gst.debug_bin_to_dot_file_with_ts(pipeline, Gst.DebugGraphDetails.ALL, "removing-testsrc2-after")




stop_event = Event()


def timed_sequence():
    log.info("Starting Sequence")
    while True:
        if stop_event.wait(2): return
        log.info("Schedule Add Source")
        GLib.idle_add(add_new_src)

        if stop_event.wait(2): return
        log.info("Schedule Remove Source")
        GLib.idle_add(remove_src)


t = Thread(target=timed_sequence, name="Sequence")
t.start()

runner = Runner(pipeline)
runner.run_blocking()

stop_event.set()
t.join()