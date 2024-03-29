
import sys
sys.path.append('../')
import gi
import configparser
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
from gi.repository import GLib
from ctypes import *
import time
import sys
import math
import random
import platform
from common.is_aarch_64 import is_aarch64

import pyds


MAX_DISPLAY_LEN=64
PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3
MUXER_OUTPUT_WIDTH=1920
MUXER_OUTPUT_HEIGHT=1080
MUXER_BATCH_TIMEOUT_USEC=4000000
TILED_OUTPUT_WIDTH=1280
TILED_OUTPUT_HEIGHT=720
GPU_ID = 0
MAX_NUM_SOURCES = 4
SINK_ELEMENT = "nveglglessink"


g_num_sources = 0
g_source_id_list = [0] * MAX_NUM_SOURCES
g_eos_list = [False] * MAX_NUM_SOURCES
g_source_enabled = [False] * MAX_NUM_SOURCES
g_source_bin_list = [None] * MAX_NUM_SOURCES

uri = ""

loop = None
pipeline = None
streammux = None
sink = None

nvvideoconvert = None

tiler = None


def decodebin_child_added(child_proxy,Object,name,user_data):
    print("Decodebin child added:", name, "\n")
    if(name.find("decodebin") != -1):
        Object.connect("child-added",decodebin_child_added,user_data)   
    if(name.find("nvv4l2decoder") != -1):
        Object.set_property("gpu_id", GPU_ID)


def cb_newpad(decodebin,pad,data):
    global streammux
    print("In cb_newpad\n")
    caps=pad.get_current_caps()
    gststruct=caps.get_structure(0)
    gstname=gststruct.get_name()

    # Need to check if the pad created by the decodebin is for video and not
    # audio.
    print("gstname=",gstname)
    if(gstname.find("video")!=-1):
        source_id = data
        pad_name = "sink_%u" % source_id
        print(pad_name)
        #Get a sink pad from the streammux, link to decodebin
        sinkpad = streammux.get_request_pad(pad_name)
        if pad.link(sinkpad) == Gst.PadLinkReturn.OK:
            print("Decodebin linked to pipeline")
        else:
            sys.stderr.write("Failed to link decodebin to pipeline\n")


def create_uridecode_bin(index,filename):
    global g_source_id_list
    print("Creating uridecodebin for [%s]" % filename)
    g_source_id_list[index] = index
    bin_name="source-bin-%02d" % index
    print(bin_name)

    bin=Gst.ElementFactory.make("uridecodebin", bin_name)
    if not bin:
        sys.stderr.write(" Unable to create uri decode bin \n")
    # We set the input uri to the source element
    bin.set_property("uri",filename)

    bin.connect("pad-added",cb_newpad,g_source_id_list[index])
    bin.connect("child-added",decodebin_child_added,g_source_id_list[index])

    #Set status of the source to enabled
    g_source_enabled[index] = True

    return bin


def stop_release_source(source_id):
    global g_num_sources
    global g_source_bin_list
    global streammux
    global pipeline

    #Attempt to change status of source to be released 
    state_return = g_source_bin_list[source_id].set_state(Gst.State.NULL)

    if state_return == Gst.StateChangeReturn.SUCCESS:
        print("STATE CHANGE SUCCESS\n")
        pad_name = "sink_%u" % source_id
        print(pad_name)
        #Retrieve sink pad to be released
        sinkpad = streammux.get_static_pad(pad_name)
        #Send flush stop event to the sink pad, then release from the streammux
        sinkpad.send_event(Gst.Event.new_flush_stop(False))
        streammux.release_request_pad(sinkpad)
        print("STATE CHANGE SUCCESS\n")
        #Remove the source bin from the pipeline
        pipeline.remove(g_source_bin_list[source_id])
        source_id -= 1
        g_num_sources -= 1

    elif state_return == Gst.StateChangeReturn.FAILURE:
        print("STATE CHANGE FAILURE\n")
    
    elif state_return == Gst.StateChangeReturn.ASYNC:
        state_return = g_source_bin_list[source_id].get_state(Gst.CLOCK_TIME_NONE)
        pad_name = "sink_%u" % source_id
        print(pad_name)
        sinkpad = streammux.get_static_pad(pad_name)
        sinkpad.send_event(Gst.Event.new_flush_stop(False))
        streammux.release_request_pad(sinkpad)
        print("STATE CHANGE ASYNC\n")
        pipeline.remove(g_source_bin_list[source_id])
        source_id -= 1
        g_num_sources -= 1


def delete_sources(data):
    global loop
    global g_num_sources
    global g_eos_list
    global g_source_enabled

    #First delete sources that have reached end of stream
    for source_id in range(MAX_NUM_SOURCES):
        if (g_eos_list[source_id] and g_source_enabled[source_id]):
            g_source_enabled[source_id] = False
            stop_release_source(source_id)

    #Quit if no sources remaining
    if (g_num_sources == 0):
        loop.quit()
        print("All sources stopped quitting")
        return False

    #Randomly choose an enabled source to delete
    source_id = random.randrange(0, MAX_NUM_SOURCES)
    while (not g_source_enabled[source_id]):
        source_id = random.randrange(0, MAX_NUM_SOURCES)
    #Disable the source
    g_source_enabled[source_id] = False
    #Release the source
    print("Calling Stop %d " % source_id)
    stop_release_source(source_id)

    #Quit if no sources remaining
    if (g_num_sources == 0):
        loop.quit()
        print("All sources stopped quitting")
        return False

    return True


def add_sources(data):
    global g_num_sources
    global g_source_enabled
    global g_source_bin_list

    with open('uri_names.txt','r+',encoding='utf-8') as file:
        try:
            new_uri=file.readlines()[-1]
            print(new_uri)
        except: new_uri=''
    if new_uri=='':
        print('Eklenecek RTSP Yok ')
        return True
    
    elif new_uri=='-':
        delete_sources('.')

    elif new_uri=='*':
        return True

    else:
        if (g_num_sources == MAX_NUM_SOURCES):
            print('Kamera pozisyonları dolu')
        else:
            source_id = g_num_sources

            #Randomly select an un-enabled source to add
            source_id = random.randrange(0, MAX_NUM_SOURCES)
            while (g_source_enabled[source_id]):
                source_id = random.randrange(0, MAX_NUM_SOURCES)

            #Enable the source
            g_source_enabled[source_id] = True

            print("Calling Start %d " % source_id)

            #Create a uridecode bin with the chosen source id
            source_bin = create_uridecode_bin(source_id, uri)

            if (not source_bin):
                sys.stderr.write("Failed to create source bin. Exiting.")
                exit(1)
            
            #Add source bin to our list and to pipeline
            g_source_bin_list[source_id] = source_bin
            pipeline.add(source_bin)

            #Set state of source bin to playing
            state_return = g_source_bin_list[source_id].set_state(Gst.State.PLAYING)

            if state_return == Gst.StateChangeReturn.SUCCESS:
                print("STATE CHANGE SUCCESS\n")
                source_id += 1

            elif state_return == Gst.StateChangeReturn.FAILURE:
                print("STATE CHANGE FAILURE\n")
            
            elif state_return == Gst.StateChangeReturn.ASYNC:
                state_return = g_source_bin_list[source_id].get_state(Gst.CLOCK_TIME_NONE)
                source_id += 1

            elif state_return == Gst.StateChangeReturn.NO_PREROLL:
                print("STATE CHANGE NO PREROLL\n")

            g_num_sources += 1

            #If reached the maximum number of sources, delete sources every 10 seconds

    
    return True

def bus_call(bus, message, loop):
    global g_eos_list
    t = message.type
    if t == Gst.MessageType.EOS:
        sys.stdout.write("End-of-stream\n")
        loop.quit()
    elif t==Gst.MessageType.WARNING:
        err, debug = message.parse_warning()
        sys.stderr.write("Warning: %s: %s\n" % (err, debug))
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        sys.stderr.write("Error: %s: %s\n" % (err, debug))
        loop.quit()
    elif t == Gst.MessageType.ELEMENT:
        struct = message.get_structure()
        #Check for stream-eos message
        if struct is not None and struct.has_name("stream-eos"):
            parsed, stream_id = struct.get_uint("stream-id")
            if parsed:
                #Set eos status of stream to True, to be deleted in delete-sources
                print("Got EOS from stream %d" % stream_id)
                g_eos_list[stream_id] = True
    return True

def main(args):
    global g_num_sources
    global g_source_bin_list
    global uri

    global loop
    global pipeline
    global streammux
    global sink
    
    global nvvideoconvert
    
    global tiler
    
     # Check input arguments
    if len(args) < 2:
        sys.stderr.write("usage: %s <uri1> \n" % args[0])
        sys.exit(1)

    num_sources=len(args)-1

    # Standard GStreamer initialization
    Gst.init(None)
    #Gst.debug_set_active(True)
    #Gst.debug_set_default_threshold(7)
    
    print("Creating Pipeline \n ")
    pipeline = Gst.Pipeline()
    is_live = False

    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline \n")
    print("Creating streammux \n ")

    # Create nvstreammux instance to form batches from one or more sources.
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    if not streammux:
        sys.stderr.write(" Unable to create NvStreamMux \n")

    streammux.set_property("batched-push-timeout", 25000)
    streammux.set_property("batch-size", 30)
    streammux.set_property("gpu_id", GPU_ID)

    pipeline.add(streammux)
    streammux.set_property("live-source", 1)
    uri = args[1]
    for i in range(num_sources):
        print("Creating source_bin ",i," \n ")
        uri_name=args[i+1]
        if uri_name.find("rtsp://") == 0 :
            is_live = True
        #Create first source bin and add to pipeline
        source_bin=create_uridecode_bin(i, uri_name)
        if not source_bin:
            sys.stderr.write("Failed to create source bin. Exiting. \n")
            sys.exit(1)
        g_source_bin_list[i] = source_bin
        pipeline.add(source_bin)

    g_num_sources = num_sources

    print("Creating tiler \n ")
    tiler=Gst.ElementFactory.make("nvmultistreamtiler", "nvtiler")
    if not tiler:
        sys.stderr.write(" Unable to create tiler \n")

    print("Creating nvvidconv \n ")
    nvvideoconvert = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    if not nvvideoconvert:
        sys.stderr.write(" Unable to create nvvidconv \n")

    print("Creating EGLSink \n")
    sink = Gst.ElementFactory.make(SINK_ELEMENT, "nvvideo-renderer")
    if not sink:
        sys.stderr.write(" Unable to create egl sink \n")

    if is_live:
        print("Atleast one of the sources is live")
        streammux.set_property('live-source', 1)

    #Set streammux width and height
    streammux.set_property('width', MUXER_OUTPUT_WIDTH)
    streammux.set_property('height', MUXER_OUTPUT_HEIGHT)
    

    #Set tiler properties
    tiler_rows=int(math.sqrt(num_sources))
    tiler_columns=int(math.ceil((1.0*num_sources)/tiler_rows))
    tiler.set_property("rows",tiler_rows)
    tiler.set_property("columns",tiler_columns)
    tiler.set_property("width", TILED_OUTPUT_WIDTH)
    tiler.set_property("height", TILED_OUTPUT_HEIGHT)

    #Set gpu IDs of tiler, nvvideoconvert, and nvosd
    tiler.set_property("gpu_id", GPU_ID)
    nvvideoconvert.set_property("gpu_id", GPU_ID)
    
    print("Adding elements to Pipeline \n")

    pipeline.add(tiler)
    pipeline.add(nvvideoconvert)
    
    pipeline.add(sink)

    # We link elements in the following order:
    # sourcebin -> streammux -> nvinfer -> nvtracker -> nvdsanalytics ->
    # nvtiler -> nvvideoconvert -> nvdsosd -> sink
    print("Linking elements in the Pipeline \n")
    streammux.link(tiler)
    tiler.link(nvvideoconvert)
    nvvideoconvert.link(sink)

    sink.set_property("sync", 0)
    sink.set_property("qos",0)

    # create an event loop and feed gstreamer bus mesages to it
    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect ("message", bus_call, loop)

    pipeline.set_state(Gst.State.PAUSED)

    # List the sources
    print("Now playing...")
    for i, source in enumerate(args):
        if (i != 0):
            print(i, ": ", source)

    print("Starting pipeline \n")

    pipeline.set_state(Gst.State.PLAYING)

    GLib.timeout_add_seconds(5, add_sources, g_source_bin_list)

    try:
        loop.run()
    except:
        pass
    # cleanup
    print("Exiting app\n")
    pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
