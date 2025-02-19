# coding=utf-8
import logging

from flask import Blueprint
from flask import make_response
from flask_restx import Api

logger = logging.getLogger(__name__)

api_blueprint = Blueprint('api', __name__, url_prefix='/api')

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-KEY'
    }
}

default_responses = {
    200: 'Success',
    401: 'Invalid API Key',
    403: 'Insufficient Permissions',
    404: 'Not Found',
    422: 'Unprocessable Entity',
    429: 'Too Many Requests',
    500: 'Internal Server Error'
}

api = Api(
    api_blueprint,
    version='1.0',
    title='Looperget API',
    description='A REST API for Looperget',
    authorizations=authorizations,
    default_mediatype='application/vnd.looperget.v1+json'
)

# Remove default accept header content type
if 'application/json' in api.representations:
    del api.representations['application/json']


# Add API v1 + json accept content type
@api.representation('application/vnd.looperget.v1+json')
def api_v1(data, code, headers):
    if data is None:
        data = {}
    resp = make_response(data, code)
    resp.headers.extend(headers)
    return resp

# To be used when v2 of the API is released
# @api.representation('application/vnd.looperget.v2+json')
# def api_v2(data, code, headers):
#     resp = make_response(data, code)
#     resp.headers.extend(headers)
#     return resp


def init_api(app):
    import looperget.looperget_flask.api.camera
    import looperget.looperget_flask.api.choices
    import looperget.looperget_flask.api.controller
    import looperget.looperget_flask.api.daemon
    import looperget.looperget_flask.api.export_import
    import looperget.looperget_flask.api.function
    import looperget.looperget_flask.api.input
    import looperget.looperget_flask.api.measurement
    import looperget.looperget_flask.api.note
    import looperget.looperget_flask.api.output
    import looperget.looperget_flask.api.pid
    import looperget.looperget_flask.api.settings

    app.register_blueprint(api_blueprint)
