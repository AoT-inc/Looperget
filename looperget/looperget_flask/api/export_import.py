# coding=utf-8
import logging
import traceback

import flask_login
from flask_accept import accept
from flask_restx import Resource, abort

from looperget.looperget_flask.api import api, default_responses
from looperget.looperget_flask.utils.utils_export import (export_influxdb,
                                                    export_settings)
from looperget.looperget_flask.utils.utils_general import user_has_permission

logger = logging.getLogger(__name__)

ns_export_import = api.namespace(
    'export_import', description='Export/Import operations')


@ns_export_import.route('/export_influxdb')
@ns_export_import.doc(
    security='apikey',
    responses=default_responses,
    params={}
)
class BackupInfluxdb(Resource):
    """Download an influxdb export."""

    @accept('application/vnd.looperget.v1+json')
    @flask_login.login_required
    def get(self):
        """
        Return an archive of an influxdb measurement database export.
        """
        if not user_has_permission('view_settings'):
            abort(403)

        try:
            file_send = export_influxdb()
            return file_send, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())


@ns_export_import.route('/export_settings')
@ns_export_import.doc(
    security='apikey',
    responses=default_responses,
    params={}
)
class BackupInfluxdb(Resource):
    """Download a Looperget configuration export."""

    @accept('application/vnd.looperget.v1+json')
    @flask_login.login_required
    def get(self):
        """
        Return an archive of the Looperget confgiuration export.
        """
        if not user_has_permission('view_settings'):
            abort(403)

        try:
            file_send = export_settings()
            return file_send, 200
        except Exception:
            abort(500,
                  message='An exception occurred',
                  error=traceback.format_exc())
