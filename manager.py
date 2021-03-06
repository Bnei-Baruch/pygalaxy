import logging
import thread
import threading
from collections import defaultdict

import gi
import time

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

log = logging.getLogger(__name__)


class BaseGSTManager(object):

    def __init__(self):
        super(BaseGSTManager, self).__init__()
        self.g_loop = None
        self.g_loop_thread = None
        self.pipelines = {}
        self.timeout_counters = defaultdict(int)
        self.timeout_last = {}

    def initialize(self):
        log.info('Starting GLib.MainLoop thread')
        self.g_loop_thread = threading.Thread(target=self.run_glib_loop)
        self.g_loop_thread.daemon = True
        self.g_loop_thread.start()

        # Initialize thread support
        # https://wiki.gnome.org/Projects/PyGObject/Threading
        log.info('Initializing GLib thread support')
        GObject.threads_init()

        # https://gstreamer.freedesktop.org/data/doc/gstreamer/head/gstreamer/html/gstreamer-Gst.html#gst-init
        log.info('Initializing GStreamer library')
        Gst.init(None)

        log.info('Initializing pipelines')
        self.init_pipelines()

        log.info('Playing pipelines')
        self.play_pipelines()

        self.clear_timeouts()

    def run_glib_loop(self):
        self.g_loop = GObject.MainLoop()
        try:
            self.g_loop.run()
        except KeyboardInterrupt:
            log.info('Ctrl+C hit, quitting')
            self.shutdown()
            thread.interrupt_main()

    def is_alive(self):
        return self.g_loop_thread and self.g_loop_thread.is_alive()

    def init_pipelines(self):
        raise NotImplemented

    def play_pipelines(self):
        for name, pipeline in self.pipelines.iteritems():
            log.info('Setting %s pipeline to PLAY', name)
            pipeline.set_state(Gst.State.PLAYING)

    def init_pipeline(self, name, cmd):
        log.info('Initializing pipeline: %s', name)
        log.debug(cmd)
        pipeline = Gst.parse_launch(cmd)
        self.pipelines[name] = pipeline
        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message(name))
        return pipeline

    @staticmethod
    def restart_element(element):
        element.set_state(Gst.State.READY)
        element.set_state(Gst.State.PAUSED)
        element.set_state(Gst.State.PLAYING)

    def shutdown(self):
        log.info('Shutting down')

        log.info('Shutting down pipelines')
        for name, pipeline in self.pipelines.iteritems():
            log.info('Setting %s pipeline to NULL', name)
            pipeline.set_state(Gst.State.NULL)

        log.info('Quiting GLib.MainLoop')
        self.g_loop.quit()

        if threading.current_thread() is not self.g_loop_thread:
            log.info('Join GLib MainLoop thread')
            self.g_loop_thread.join()

    def on_message(self, name):
        def f(bus, msg):
            if msg.type == Gst.MessageType.ERROR:
                err, debug = msg.parse_error()
                log.error('Bus [%s], error: %s', name, err)
            elif msg.type == Gst.MessageType.WARNING:
                err, debug = msg.parse_warning()
                log.warning('Bus [%s], warning: %s', name, err)
            elif msg.has_name('GstUDPSrcTimeout'):
                self.on_timeout(name, msg)
            elif msg.type not in (Gst.MessageType.QOS,
                                  Gst.MessageType.STATE_CHANGED,
                                  Gst.MessageType.STREAM_STATUS,
                                  Gst.MessageType.STREAM_START):
                structure = msg.get_structure()
                if structure:
                    log.debug('Bus [%s], %s: %s', name, msg.src.get_name(), structure.to_string())
            return Gst.BusSyncReply.PASS

        return f

    def on_timeout(self, name, msg):
        """
        We keep track of consecutive timeouts for every udpsrc.
        UdpSrcTimeout value is 1 second, so we define two consecutive timeouts such that
        they occur no longer than 1.3 second one after the other.

        When a timeout event comes later than 1.3 second after the previous event
         it is considered new and we reset the counter.
        """
        port = msg.src.props.port
        last_timeout = self.timeout_last.get(port)
        self.timeout_last[port] = time.time()
        if last_timeout and time.time() - last_timeout < 1.3:
            self.timeout_counters[port] += 1  # Consecutive timeout
            log.debug('Consecutive timeout %s [port %d]: %d', name, port, self.timeout_counters[port])
        else:
            self.timeout_counters[port] = 1
            log.warning('New timeout %s [port %d]: %d', name, port, self.timeout_counters[port])

    def get_timeouts(self):
        return self.timeout_counters

    def clear_timeouts(self):
        """
        This function runs every 1 seconds and clear timeout counters
         for ports which have not timeout in the last 2 seconds.
        This is necessary for counting only consecutive timeouts.
        """
        t = time.time()
        for port, last_timeout in self.timeout_last.items():
            if t - last_timeout > 2:
                log.debug('port [%d] seems to have stable stream, clearing timeout counters', port)
                del self.timeout_last[port]
                del self.timeout_counters[port]

        # Call ourselves again in 1 second
        timer = threading.Timer(1.0, self.clear_timeouts)
        timer.daemon = True  # so program could exit cleanly
        timer.start()


class SDIManager(BaseGSTManager):
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
        'decklinkvideosink device-number=2 mode=3'
    ])

    AUDIO_CMD = ' ! '.join([
        'udpsrc port=8042 caps="application/x-rtp, media=audio, payload=111, clock-rate=48000, encoding-name=X-GST-OPUS-DRAFT-SPITTKA-00"',
        'rtpjitterbuffer',
        'rtpopusdepay',
        'queue',
        'opusdec plc=true',
        'alsasink'
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

    MEANINGFUL_TIMEOUT_PERIOD = 10  # in seconds
    TIMEOUT_RESET_TIME = 60 * 10  # in seconds

    def __init__(self):
        super(SDIManager, self).__init__()
        self.overlays = {}
        self.titles = {}

    def init_pipelines(self):
        self.init_pipeline('large', self.LARGE_CMD)
        self.init_pipeline('small', self.SMALL_CMD)
        self.init_pipeline('control', self.CONTROL_CMD)
        self.init_pipeline('fours', self.FOURS_CMD)
        self.init_pipeline('audio', self.AUDIO_CMD)

        # Keep a quick reference map from port to text overlay element
        for port, channel in self.PORT_CHANNEL_MAP.iteritems():
            element_name = 'overlay{}'.format(self.FOURS_PORT_SLOT_MAP.get(port, ''))
            self.overlays[port] = self.pipelines[channel].get_by_name(element_name)

    def set_title(self, port, title):
        log.info('Setting title for %d to %s', port, title)
        self.titles[port] = title
        self.overlays[port].set_property('text', '<span foreground="white" background="blue">' + title + '</span>')
        # self.wake_up()

    def get_titles(self):
        return self.titles

    def on_timeout(self, name, msg):
        """
        Timeouts are meaningful only during lessons.
         Outside lessons, this handler is called all the time since nobody is forwarding from janus.
         Thus causing timeouts on our udpsrc.

        Restarting the pipeline all the time is ugly.
         So we keep a count of timeouts and restart the pipeline in the first 10 seconds.
         After that we ignore these events for 10 minutes and then reset the counter.
         This allow us to keep the application running all the time without the need to restart it
         periodically with cron.

        We also wake up on moderator interaction (for example, set_title). See self.wake_up()
        """
        super(SDIManager, self).on_timeout(name, msg)
        port = msg.src.props.port
        count = self.timeout_counters[port]
        if count == self.TIMEOUT_RESET_TIME:
            log.debug('Resetting timeout counter for %s [port %d] after %d minutes of continuous timeout', name, port, 10)
            count = self.timeout_counters[port] = 0
        if count < self.MEANINGFUL_TIMEOUT_PERIOD:
            log.warning('Meaningful timeout, restarting %s [port %d], %d', name, port, count)
            self.restart_element(self.pipelines[name])
        else:
            log.debug('Ignoring timeout: %s %d', name, count)

    # def wake_up(self):
    #     """
    #     Iff all ports are in timeouts then restart everything.
    #     We mimic the login in webapp /restart/ action
    #     """
    #     if len([count for count in self.timeout_counters.values() if count > 0]) == len(self.PORT_CHANNEL_MAP):
    #         log.info("WAKEING UP !")
    #
    #         # Copy titles so we won't loose them
    #         titles = self.titles.copy()
    #
    #         # Shutdown properly
    #         self.shutdown()
    #
    #         # Redeclare all members
    #         self.__init__()
    #
    #         # Initialize properly
    #         self.initialize()
    #
    #         # Restore titles
    #         for port, title in titles.iteritems():
    #             self.set_title(port, title)


class SDIManagerDev(SDIManager):
    SINGLE_CMD = ' ! '.join([
        'videotestsrc pattern={}',
        'video/x-raw,width=400,height=300',
        'textoverlay name=overlay ypad=0 font-desc="LiberationSerif 32px" shaded-background=false draw-shadow=false valignment=top halignment=right text=""',
        'autovideosink'])

    LARGE_CMD = SINGLE_CMD.format('9')
    SMALL_CMD = SINGLE_CMD.format('snow')
    # CONTROL_CMD = SINGLE_CMD.format('ball')
    CONTROL_CMD = 'udpsrc port=8044 timeout=1000000000 ! application/x-rtp, payload=127 ! rtph264depay ! avdec_h264 ! xvimagesink sync=false'

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
        'udpsrc port=5028 timeout=1000000000 ! application/x-rtp, encoding-name=JPEG, payload=26 ! rtpjpegdepay ! jpegdec ! videoscale ! videorate ! videoconvert ! video/x-raw, format=UYVY, width=320, height=180, framerate=20/1 ! mix.',
        'udpsrc port=5030 timeout=1000000000 ! application/x-rtp, payload=127 ! rtph264depay ! avdec_h264 ! videoscale ! videorate ! videoconvert ! video/x-raw, format=UYVY, width=320, height=180, framerate=20/1 ! mix.'
    ])

    AUDIO_CMD = ' ! '.join([
        'audiotestsrc',
        'audioconvert',
        'autoaudiosink'
    ])


class CompositeGSTManager(BaseGSTManager):

    PREVIEW_CMD = '''
        compositor name=mix timeout=100000000 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=0 sink_1::ypos=180 sink_2::xpos=320 sink_2::ypos=0 sink_3::xpos=320 sink_3::ypos=180 sync=false !
        video/x-raw, format=UYVY, width=640, height=360, framerate=25/1 !
        videoscale !
        videorate !
        videoconvert !
        vp8enc end-usage=cbr cpu-used=15 deadline=1 target-bitrate=600000 max-intra-bitrate=600000 threads=4 error-resilient=0x00000001 !
        rtpvp8pay !
        queue !
        tee name=t !
        queue !
        udpsink host=jnseur.kbb1.com port=20024 t. !
        queue !
        udpsink host=127.0.0.1 port=20024 \

        udpsrc port=6024 name="udpsrc6024" timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" !
        rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true !
        rtpvp8depay !
        queue !
        vp8dec !
        videoscale !
        videorate !
        videoconvert !
        video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 !
        mix. \

        udpsrc port=6026 name="udpsrc6026" timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" !
        rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true !
        rtpvp8depay !
        queue !
        vp8dec !
        videoscale !
        videorate !
        videoconvert !
        video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 !
        mix. \

        udpsrc port=6028 name="udpsrc6028" timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" !
        rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true !
        rtpvp8depay !
        queue !
        vp8dec !
        videoscale !
        videorate !
        videoconvert !
        video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 !
        mix. \

        udpsrc port=6030 name="udpsrc6030" timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" !
        rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true !
        rtpvp8depay !
        queue !
        vp8dec !
        videoscale !
        videorate !
        videoconvert !
        video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 !
        mix.
    '''

    PROGRAM_CMD = '''
        compositor name=mix timeout=100000000 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=0 sink_1::ypos=180 sink_2::xpos=320 sink_2::ypos=0 sink_3::xpos=320 sink_3::ypos=180 sync=false !
        video/x-raw, format=UYVY, width=640, height=360, framerate=25/1 !
        videoscale !
        videorate !
        videoconvert !
        vp8enc end-usage=cbr cpu-used=15 deadline=1 target-bitrate=600000 max-intra-bitrate=600000 threads=4 error-resilient=0x00000001 !
        rtpvp8pay !
        queue !
        tee name=t !
        queue !
        udpsink host=62.219.8.116 port=8024 t. !
        queue !
        udpsink host=127.0.0.1 port=8024 t. !
        queue !
        udpsink host=jnseur.kbb1.com port=8024 \

        udpsrc port=5024 name="udpsrc5024" timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" !
        rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true !
        rtpvp8depay !
        queue !
        vp8dec !
        videoscale !
        videorate !
        videoconvert !
        video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 !
        mix.

        udpsrc port=5026 name="udpsrc5026" timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" !
        rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true !
        rtpvp8depay !
        queue !
        vp8dec !
        videoscale !
        videorate !
        videoconvert !
        video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 !
        mix.

        udpsrc port=5028 name="udpsrc5028" timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" !
        rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true !
        rtpvp8depay !
        queue !
        vp8dec !
        videoscale !
        videorate !
        videoconvert !
        video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 !
        mix.

        udpsrc port=5030 name="udpsrc5030" timeout=1000000000 caps="application/x-rtp, media=video, payload=100, clock-rate=90000, encoding-name=VP8-DRAFT-IETF-01" !
        rtpjitterbuffer do-lost=false latency=50 drop-on-latency=true !
        rtpvp8depay !
        queue !
        vp8dec !
        videoscale !
        videorate !
        videoconvert !
        video/x-raw, format=UYVY, width=320, height=180, framerate=25/1 !
        mix.
    '''

    def init_pipelines(self):
        self.init_pipeline('program', self.PROGRAM_CMD)
        self.init_pipeline('preview', self.PREVIEW_CMD)

    def on_timeout(self, name, msg):
        """
        Note that we restart the specific UdpSrc rather than the whole pipeline.
        """
        super(CompositeGSTManager, self).on_timeout(name, msg)

        port = msg.src.props.port
        if self.timeout_counters[port] % 10 == 0:
            log.warning('10th consecutive timeout, restarting updsrc on port %d', msg.src.props.port)
            self.restart_element(msg.src)


class CompositeGSTManagerDev(CompositeGSTManager):

    PREVIEW_CMD = ' ! '.join([
        'compositor name=mix timeout=100000000 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=0 sink_1::ypos=180 sink_2::xpos=320 sink_2::ypos=0 sink_3::xpos=320 sink_3::ypos=180 sync=false',
        'autovideosink'
    ]) + ' ' + ' '.join([
        'videotestsrc pattern=0 ! mix.',
        'videotestsrc pattern=1 ! mix.',
        'udpsrc port=5028 timeout=1000000000 ! application/x-rtp, encoding-name=JPEG, payload=26 ! rtpjpegdepay ! jpegdec ! videoscale ! videorate ! videoconvert ! video/x-raw, format=UYVY, width=320, height=180, framerate=20/1 ! mix.',
        'udpsrc port=5030 timeout=1000000000 ! application/x-rtp, payload=127 ! rtph264depay ! avdec_h264 ! videoscale ! videorate ! videoconvert ! video/x-raw, format=UYVY, width=320, height=180, framerate=20/1 ! mix.'
    ])

    PROGRAM_CMD = ' ! '.join([
        'compositor name=mix timeout=100000000 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=0 sink_1::ypos=180 sink_2::xpos=320 sink_2::ypos=0 sink_3::xpos=320 sink_3::ypos=180 sync=false',
        'autovideosink'
    ]) + ' ' + ' '.join([
        'videotestsrc pattern=4 ! mix.',
        'videotestsrc pattern=5 ! mix.',
        'videotestsrc pattern=6 ! mix.',
        'videotestsrc pattern=7 ! mix.'
    ])




