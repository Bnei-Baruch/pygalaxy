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


class EnableCors(object):
    """
        Enable CORS via a bottle plugin
        See http://stackoverflow.com/questions/17262170/bottle-py-enabling-cors-for-jquery-ajax-requests
    """
    name = 'enable_cors'
    api = 2

    def apply(self, fn, context):
        def _enable_cors(*args, **kwargs):
            # set CORS headers
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token ,DNT ,X-CustomHeader ,Keep-Alive ,User-Agent ,X-Requested-With, If-Modified-Since,Cache-Control'

            if bottle.request.method != 'OPTIONS':
                # actual request; reply with the actual response
                return fn(*args, **kwargs)

        return _enable_cors


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


app.install(EnableCors())

log.info('Running application')
app.run(host=app.config['host'], port=app.config['port'])
