# coding=utf-8
import subprocess

from flask_babel import lazy_gettext
from looperget.config_translations import TRANSLATIONS
from looperget.config import INSTALL_DIRECTORY
from looperget.databases.models import Actions
from looperget.actions.base_action import AbstractFunctionAction
from looperget.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'system_shutdown',
    'name': "{}: {}".format(TRANSLATIONS['system']['title'], lazy_gettext('Shutdown')),
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Shutdown the System',

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will shut down the system in 10 seconds.',
}


class ActionModule(AbstractFunctionAction):
    """Function Action: System Shutdown."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.none = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.action_setup = True

    def run_action(self, dict_vars):
        dict_vars['message'] += " System shutting down in 10 seconds."
        cmd = f'{INSTALL_DIRECTORY}/looperget/scripts/looperget_wrapper shutdown 2>&1'
        subprocess.Popen(cmd, shell=True)

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup
