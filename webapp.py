#!/usr/bin/env python
import logging.config
import os
import pprint

import bottle
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


@app.get('/titles/')
def get_titles():
    return GSTManager.get_titles()


@app.post('/titles/')
def set_titles():
    log.debug(request.json)
    for x in request.json:
        GSTManager.set_title(int(x['port']), x['title'])
    return "SUCCESS"


@app.get('/health_check/')
def health_check():
    if not GSTManager.is_alive():
        response.status = '500 Gstreamer manager is dead'
        return

    return "SUCCESS"


log.info('Running application')
app.run(host=app.config['host'], port=app.config['port'])
