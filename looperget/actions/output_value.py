# coding=utf-8
import threading

from flask_babel import lazy_gettext

from looperget.config_translations import TRANSLATIONS
from looperget.databases.models import Actions
from looperget.databases.models import Output
from looperget.actions.base_action import AbstractFunctionAction
from looperget.utils.constraints_pass import constraints_pass_positive_or_zero_value
from looperget.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'output_value',
    'name': f"{TRANSLATIONS['output']['title']}: {TRANSLATIONS['value']['title']}",
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('출력에 값을 전송합니다.'),

    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 값 출력이 활성화됩니다. '
             '<strong>self.run_action("ACTION_ID", value={"output_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "channel": 0, "value": 42})</strong>를 실행하면 지정된 ID와 채널의 출력으로 값이 전송됩니다. '
             '시스템에 존재하는 실제 Output ID로 output_id 값을 변경하는 것을 잊지 마십시오.',

    'custom_options': [
        {
            'id': 'output',
            'type': 'select_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels',
            ],
            'name': 'Output',
            'phrase': '제어할 출력을 선택하세요'
        },
        {
            'id': 'value',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': lazy_gettext('Value'),
            'phrase': '출력으로 전송할 값을 입력하세요'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """함수 동작: 출력 (값)."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.output_device_id = None
        self.output_channel_id = None
        self.value = None

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
            output_id = dict_vars["value"]["output_id"]
        except:
            output_id = self.output_device_id

        try:
            channel = dict_vars["value"]["channel"]
        except:
            channel = self.get_output_channel_from_channel_id(
                self.output_channel_id)

        try:
            value = dict_vars["value"]["value"]
        except:
            value = self.value

        output = db_retrieve_table_daemon(
            Output, unique_id=output_id, entry='first')

        if not output:
            msg = f"오류: ID '{output_id}'에 해당하는 출력이 존재하지 않습니다."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        dict_vars['message'] += f"출력 {output_id} CH{channel} ({output.name})에 값을 {value}로 전송합니다."

        output_on = threading.Thread(
            target=self.control.output_on,
            args=(output_id,),
            kwargs={'output_type': 'value',
                    'amount': value,
                    'output_channel': channel})
        output_on.start()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup