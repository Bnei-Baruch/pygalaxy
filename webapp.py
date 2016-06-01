#!/usr/bin/env python
import logging.config

from bottle import route, run, post, request

from manager import GstreamerManager

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s %(process)d %(threadName)s [%(name)s:%(lineno)s] %(message)s')

log = logging.getLogger(__name__)

log.info('Initializing Gstreamer Manager')
GSTManager = GstreamerManager()
GSTManager.initialize()
log.info('Gstreamer Manager initialization complete')


@route('/hello/:name')
def index(name='World'):
    return {'hello': name}


@post('/titles/')
def set_titles():
    log.debug(request.json)
    for x in request.json:
        GSTManager.set_title(int(x['port']), x['title'])
    return "SUCCESS"

log.info('Running application')
run(host='localhost', port=8081)
