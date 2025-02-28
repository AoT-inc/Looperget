# coding=utf-8
from flask_babel import lazy_gettext

from looperget.actions.base_action import AbstractFunctionAction
from looperget.config_translations import TRANSLATIONS
from looperget.databases.models import Actions
from looperget.utils.database import db_retrieve_table_daemon


ACTION_INFORMATION = {
    'name_unique': 'create_log_line',
    'name': f"{TRANSLATIONS['create']['title']}: Daemon Log Line",
    'message': lazy_gettext('데몬 로그에 로그 라인을 생성합니다.'),
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong>를 실행하면 데몬 로그에 로그 라인이 추가됩니다. '
             'Executing <strong>self.run_action("ACTION_ID", value={"log_level": "info", "log_text": "this is a log line"})</strong>를 실행하면 지정된 로그 레벨과 로그 라인 텍스트로 작업이 실행됩니다. '
             '로그 라인 텍스트가 지정되지 않으면 작업 메시지가 텍스트로 사용됩니다.',

    'custom_options': [
        {
            'id': 'log_level',
            'type': 'select',
            'default_value': 'info',
            'required': True,
            'options_select': [
                ('info', 'Info'),
                ('warning', 'Warning'),
                ('error', 'Error'),
                ('debug', 'Debug')
            ],
            'name': '로그 레벨',
            'phrase': '로그에 텍스트를 삽입할 로그 레벨을 지정합니다.'
        },
        {
            'id': 'log_text',
            'type': 'text',
            'default_value': 'Log Line Text',
            'required': False,
            'name': '로그 라인 텍스트',
            'phrase': '데몬 로그에 삽입할 텍스트'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Create Note."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.log_level = None
        self.log_text = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.action_setup = True

    def run_action(self, dict_vars):
        try:
            log_level = dict_vars["value"]["log_level"]
        except:
            log_level = self.log_level

        try:
            log_text = dict_vars["value"]["log_text"]
        except:
            log_text = self.log_text

        if not log_text:
            log_text = dict_vars['message']

        dict_vars['message'] += f" 로그 레벨 {log_level}로 데몬 로그에 '{log_text}' 텍스트를 추가합니다."

        if log_level == 'info':
            self.logger.info(log_text)
        elif log_level == 'warning':
            self.logger.warning(log_text)
        elif log_level == 'error':
            self.logger.error(log_text)
        elif log_level == 'debug':
            self.logger.debug(log_text)

        if log_level != 'debug':
            self.logger.debug(f"메시지: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup