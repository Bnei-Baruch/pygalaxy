#!/usr/bin/env python
import logging.config

from bottle import run, post, request, response, get

from manager import GstreamerManager

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s %(process)d %(threadName)s [%(name)s:%(lineno)s] %(message)s')

log = logging.getLogger(__name__)

log.info('Initializing Gstreamer Manager')
GSTManager = GstreamerManager()
GSTManager.initialize()
log.info('Gstreamer Manager initialization complete')


@get('/titles/')
def get_titles():
    return GSTManager.get_titles()


@post('/titles/')
def set_titles():
    log.debug(request.json)
    for x in request.json:
        GSTManager.set_title(int(x['port']), x['title'])
    return "SUCCESS"


@get('/health_check/')
def health_check():
    if not GSTManager.is_alive():
        response.status = '500 Gstreamer manager is dead'
        return

    return "SUCCESS"


log.info('Running application')
run(host='localhost', port=8081)
