import logging
import threading

import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

log = logging.getLogger(__name__)


class GstreamerManager(object):
    SINGLE_CMD = ' ! '.join([
        'udpsrc timeout=1000000000 port={port} caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01"',
        'rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true',
        'rtpvp8depay',
        'vp8dec',
        'queue',
        'videoconvert',
        'videoscale add-borders=false method=4',
        'videorate',
        'interlace field-pattern=2:2',
        'video/x-raw, format=UYVY, width=720, height=576, framerate=25/1, interlace-mode=interleaved, pixel-aspect-ratio=12/11, colorimetry=bt601, chroma-site=mpeg2',
        'textoverlay name=overlay text="" ypad=0 valignment=top halignment=right font-desc="LiberationSerif 65px" shaded-background=false draw-shadow=false',
        'compositor name=mix timeout=100000000',
        'decklinkvideosink device-number={device_number} mode=3'
    ])

    LARGE_CMD = SINGLE_CMD.format(port=8004, device_number=3)
    SMALL_CMD = SINGLE_CMD.format(port=8014, device_number=0)
    CONTROL_CMD = SINGLE_CMD.format(port=8044, device_number=1)

    FOURS_CMD = ' ! '.join([
        'udpsrc timeout=1000000000 port=8024 caps="application/x-rtp, media=video, payload=96, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01"',
        'rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true',
        'rtpvp8depay',
        'vp8dec',
        'queue',
        'videoconvert',
        'videoscale add-borders=false method=4',
        'videorate',
        'interlace field-pattern=2:2',
        'video/x-raw, format=UYVY, width=720, height=576, framerate=25/1, interlace-mode=interleaved, pixel-aspect-ratio=12/11, colorimetry=bt601, chroma-site=mpeg2',
        'textoverlay name=overlay1 text="" ypad=10 xpad=10 valignment=top halignment=right font-desc="LiberationSerif 35px" draw-shadow=false shaded-background=false',
        'textoverlay name=overlay2 text="" ypad=10 xpad=360 valignment=top halignment=right font-desc="LiberationSerif 35px" draw-shadow=false shaded-background=false',
        'textoverlay name=overlay3 text="" ypad=280 xpad=360 valignment=top halignment=right font-desc="LiberationSerif 35px" draw-shadow=false shaded-background=false',
        'textoverlay name=overlay4 text="" ypad=280 xpad=10 valignment=top halignment=right font-desc="LiberationSerif 35px" draw-shadow=false shaded-background=false',
        'compositor name=mix timeout=100000000',
        'decklinkvideosink device-number=2 mode=3'
    ])

    FOURS_PORT_SLOT_MAP = {
        5024: '2',
        5026: '3',
        5028: '1',
        5030: '4',
    }

    PORT_CHANNEL_MAP = {
        8004: 'large',
        8014: 'small',
        8044: 'control',
        5024: 'fours',
        5026: 'fours',
        5028: 'fours',
        5030: 'fours',
    }

    def __init__(self):
        super(GstreamerManager, self).__init__()
        self.pipelines = {}
        self.overlays = {}
        self.titles = {}
        self.g_loop = None
        self.g_loop_thread = None

    def initialize(self):
        # https://gstreamer.freedesktop.org/data/doc/gstreamer/head/gstreamer/html/gstreamer-Gst.html#gst-init
        log.info('Initializing GStreamer library')
        Gst.init(None)

        # Initialize thread support
        # https://wiki.gnome.org/Projects/PyGObject/Threading
        GObject.threads_init()

        log.info('Initializing pipelines')
        self.init_pipeline('large', self.LARGE_CMD)
        self.init_pipeline('small', self.SMALL_CMD)
        self.init_pipeline('control', self.CONTROL_CMD)
        self.init_pipeline('fours', self.FOURS_CMD)

        # Keep a quick reference map from port to text overlay element
        for port, channel in self.PORT_CHANNEL_MAP.iteritems():
            element_name = 'overlay{}'.format(self.FOURS_PORT_SLOT_MAP.get(port, ''))
            self.overlays[port] = self.pipelines[channel].get_by_name(element_name)

        log.info('Playing pipelines')
        for name, pipeline in self.pipelines.iteritems():
            log.debug('Setting %s pipeline to PLAY', name)
            pipeline.set_state(Gst.State.PLAYING)

        log.info('Kicking off GObject.MainLoop thread')
        self.g_loop = GObject.MainLoop()
        self.g_loop_thread = threading.Thread(target=self.g_loop.run)
        self.g_loop_thread.daemon = True
        self.g_loop_thread.start()

    def init_pipeline(self, name, cmd):
        log.debug('Initializing %s pipeline', name)
        log.debug(cmd)
        pipeline = Gst.parse_launch(cmd)
        self.pipelines[name] = pipeline
        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message(name))
        return pipeline

    def shutdown(self):
        log.info('Shutting down')

        log.info('Shutting down pipelines')
        for name, pipeline in self.pipelines.iteritems():
            log.debug('Setting %s pipeline to NULL', name)
            pipeline.set_state(Gst.State.NULL)

        log.info('Shutting down GObject.MainLoop')
        self.g_loop.quit()
        self.g_loop_thread.join()

    def set_title(self, port, title):
        log.info('Setting title for %d to %s', port, title)
        self.titles[port] = title
        self.overlays[port].set_property('text', '<span foreground="white" background="blue">' + title + '</span>')

    def get_titles(self):
        return self.titles

    def on_message(self, name):
        def f(bus, msg):
            if msg.type == Gst.MESSAGE_ERROR:
                err, debug = msg.parse_error()
                log.error('Bus Error [%s]: %s', name, err)
            elif msg.type == Gst.MESSAGE_WARNING:
                log.warning('Bus Warning [%s]: %s', name, msg)
            elif msg.type == Gst.MESSAGE_STATE_CHANGED:
                old, new, pending = msg.parse_state_changed()
                log.debug('Bus State Changed [%s], %s => %s (pending: %s)', name, old, new, pending)
            elif msg.has_name('GstUDPSrcTimeout'):
                self.on_timeout(name)
            else:
                log.debug('Bus Message [%s], %s => %s (pending: %s)', name, msg.type)
            return Gst.BusSyncReply.PASS

        return f

    def on_timeout(self, name):
        log.warning('%s [%s] timeout', self.titles[name], name)
        #TODO: implement restart management here

    def is_alive(self):
        return self.g_loop_thread and self.g_loop_thread.is_alive()


class GstreamerManagerDev(GstreamerManager):
    SINGLE_CMD = ' ! '.join([
        'videotestsrc pattern={}',
        'video/x-raw,width=400,height=300',
        'textoverlay name=overlay ypad=0 font-desc="LiberationSerif 32px" shaded-background=false draw-shadow=false valignment=top halignment=right text=""',
        'autovideosink'])

    LARGE_CMD = SINGLE_CMD.format('9')
    SMALL_CMD = SINGLE_CMD.format('snow')
    CONTROL_CMD = SINGLE_CMD.format('ball')

    FOURS_CMD = ' ! '.join([
        'compositor name=mix timeout=100000000 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=0 sink_1::ypos=180 sink_2::xpos=320 sink_2::ypos=0 sink_3::xpos=320 sink_3::ypos=180 sync=false',
        'textoverlay name=overlay1 ypad=0 xpad=330 text="" font-desc="LiberationSerif 32px" shaded-background=false draw-shadow=false valignment=top halignment=right',
        'textoverlay name=overlay2 ypad=180 xpad=330 text="" font-desc="LiberationSerif 32px" shaded-background=false draw-shadow=false valignment=top halignment=right',
        'textoverlay name=overlay3 ypad=0 xpad=10 text="" font-desc="LiberationSerif 32px" shaded-background=false draw-shadow=false valignment=top halignment=right',
        'textoverlay name=overlay4 ypad=180 xpad=10 text="" font-desc="LiberationSerif 32px" shaded-background=false draw-shadow=false valignment=top halignment=right',
        'autovideosink'
    ]) + ' ' + ' '.join([
        'videotestsrc pattern=0 ! mix.',
        'videotestsrc pattern=snow ! mix.',
        'videotestsrc pattern=spokes ! mix.',
        'videotestsrc pattern=ball ! mix.'
    ])