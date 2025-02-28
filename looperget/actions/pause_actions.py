# coding=utf-8
import time

from flask_babel import lazy_gettext

from looperget.config_translations import TRANSLATIONS
from looperget.databases.models import Actions
from looperget.actions.base_action import AbstractFunctionAction
from looperget.utils.constraints_pass import constraints_pass_positive_value
from looperget.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'pause_actions',
    'name': f"액션: {TRANSLATIONS['pause']['title']}",
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('self.run_all_actions()가 사용될 때 액션 실행 간의 지연 시간을 설정합니다.'),

    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 설정된 시간 동안 일시 정지합니다. '
             '<strong>self.run_all_actions()</strong>를 실행하면 모든 액션의 순차 실행 사이에 일시 정지가 추가됩니다.',

    'custom_options': [
        {
            'id': 'duration',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{} ({})".format(lazy_gettext('지속 시간'), lazy_gettext('초')),
            'phrase': '일시 정지할 시간을 입력하세요'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Pause"""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.duration = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.action_setup = True

    def run_action(self, dict_vars):
        dict_vars['message'] += f" {self.duration}초 동안 일시 정지합니다."

        time.sleep(self.duration)

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup