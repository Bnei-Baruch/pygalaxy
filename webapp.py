#!/usr/bin/env python
import logging.config
import os
import pprint

import bottle
import sys
from bottle import request, response

from manager import GstreamerManager, GstreamerManagerDev

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s %(process)d %(threadName)s [%(name)s:%(lineno)s] %(message)s')

log = logging.getLogger(__name__)

app = bottle.default_app()
app.config['host'] = os.environ.get('GALAXY_HOST', '0.0.0.0')
app.config['port'] = int(os.environ.get('GALAXY_PORT', 8081))
app.config['galaxy.env'] = os.environ.get('GALAXY_ENV', 'dev')

log.debug('Application config')
log.debug(pprint.pformat(app.config))

log.info('Initializing Gstreamer Manager')
GSTManager = GstreamerManagerDev() if app.config['galaxy.env'] == 'dev' else GstreamerManager()
GSTManager.initialize()
log.info('Gstreamer Manager initialization complete')


@app.hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token ,DNT ,X-CustomHeader ,Keep-Alive ,User-Agent ,X-Requested-With, If-Modified-Since,Cache-Control'


@app.get('/titles/')
def get_titles():
    return GSTManager.get_titles()


@app.post('/titles/')
def set_titles():
    log.debug('set_titles: %s', request.json)
    for x in request.json:
        GSTManager.set_title(int(x['port']), x['title'])
    return "SUCCESS"


@app.get('/title.php')
def set_titles_legacy():
    log.debug('set_titles_legacy: %s', request.query_string)
    port = int(request.query.port)
    title = request.query.title
    GSTManager.set_title(port, title)
    return "SUCCESS"


@app.get('/health_check/')
def health_check():
    if not GSTManager.is_alive():
        response.status = '500 Gstreamer manager is dead'
        return
    return "SUCCESS"


@app.post('/restart/')
def restart():
    GSTManager.shutdown()
    GSTManager.initialize()
    for port, title in GSTManager.get_titles().iteritems():
        GSTManager.set_title(port, title)
    return "SUCCESS"

log.info('Running application')
app.run(host=app.config['host'], port=app.config['port'])
