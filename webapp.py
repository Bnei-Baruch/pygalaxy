#!/usr/bin/env python
import logging.config
import os
import pprint

import bottle
from bottle import request, response

from manager import SDIManager, SDIManagerDev, CompositeGSTManager, CompositeGSTManagerDev

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
env = app.config['galaxy.env']
if env == 'production-sdi':
    GSTManager = SDIManager()
elif env == 'production-composite':
    GSTManager = CompositeGSTManager()
elif env == 'dev-composite':
    GSTManager = CompositeGSTManagerDev()
else:
    GSTManager = SDIManagerDev()

GSTManager.initialize()
log.info('Gstreamer Manager initialization complete')


class EmptyOptions(object):
    """
        Bottle plugin to return successful empty response for OPTIONS method
    """
    name = 'empty_options'
    api = 2

    def apply(self, fn, context):

        def wrapper(*args, **kwargs):
            if bottle.request.method == 'OPTIONS':
                return
            return fn(*args, **kwargs)

        return wrapper


@app.route('/titles/', method=['OPTIONS', 'GET'])
def get_titles():
    return GSTManager.get_titles()


@app.route('/titles/', method=['OPTIONS', 'POST'])
def set_titles():
    log.debug('set_titles: %s', request.json)
    for x in request.json:
        GSTManager.set_title(int(x['port']), x['title'])
    return "SUCCESS"


@app.route('/title.php', method=['OPTIONS', 'GET'])
def set_titles_legacy():
    log.debug('set_titles_legacy: %s', request.query_string)
    port = int(request.query.port)
    title = request.query.title
    GSTManager.set_title(port, title)
    return "SUCCESS"


@app.route('/health_check/', method=['OPTIONS', 'GET'])
def health_check():
    if not GSTManager.is_alive():
        response.status = '500 Gstreamer manager is dead'
        return
    return "SUCCESS"


@app.route('/restart/', method=['OPTIONS', 'POST'])
def restart():
    GSTManager.shutdown()
    GSTManager.initialize()
    for port, title in GSTManager.get_titles().iteritems():
        GSTManager.set_title(port, title)
    return "SUCCESS"


@app.route('/refresh/', method=['OPTIONS', 'POST'])
def refresh():
    GSTManager.refresh()
    return "SUCCESS"


@app.route('/timeouts/', method=['OPTIONS', 'GET'])
def get_timeouts():
    return GSTManager.get_timeouts()

app.install(EmptyOptions())

log.info('Running application')
app.run(host=app.config['host'], port=app.config['port'])
