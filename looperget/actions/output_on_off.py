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
    'name_unique': 'output_on_off',
    'name': f"{TRANSLATIONS['output']['title']}: "
            f"{TRANSLATIONS['on']['title']}/{TRANSLATIONS['off']['title']}/{TRANSLATIONS['duration']['title']}",
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('On/Off 출력 장치를 켜거나 끄거나, 또는 지정된 시간 동안 켭니다.'),

    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 출력 장치가 작동됩니다. '
             '<strong>self.run_action("ACTION_ID", value={"output_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "channel": 0, "state": "on", "duration": 300})</strong>를 실행하면 지정된 ID와 채널의 출력 장치 상태가 설정됩니다. '
             '시스템에 존재하는 실제 출력 ID로 output_id 값을 변경하는 것을 잊지 마십시오. '
             '상태가 on이고 지속 시간이 설정된 경우, 해당 기간 후에 출력 장치가 꺼집니다.',

    'custom_options': [
        {
            'id': 'output',
            'type': 'select_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels'
            ],
            'name': '출력',
            'phrase': '제어할 출력을 선택하세요'
        },
        {
            'id': 'state',
            'type': 'select',
            'default_value': '',
            'required': True,
            'options_select': [
                ('on', 'On'),
                ('off', 'Off')
            ],
            'name': lazy_gettext('상태'),
            'phrase': '출력을 켜거나 끕니다.'
        },
        {
            'id': 'duration',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': "{} ({})".format(lazy_gettext('지속 시간'), lazy_gettext('초')),
            'phrase': '출력이 켜진 경우, 지속 시간을 설정할 수 있습니다. 0으로 설정하면 계속 켜집니다.'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """함수 동작: 출력 (켜기/끄기/지속 시간)."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.output_device_id = None
        self.output_channel_id = None
        self.state = None
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
            state = dict_vars["value"]["state"]
        except:
            state = self.state

        try:
            duration = dict_vars["value"]["duration"]
        except:
            duration = self.duration

        output = db_retrieve_table_daemon(
            Output, unique_id=output_id, entry='first')

        if not output:
            msg = f"오류: ID '{output_id}'에 해당하는 출력이 존재하지 않습니다."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        dict_vars['message'] += f"출력 {output_id} CH{channel} ({output.name})를 {state} 상태로 전환합니다"
        if state == 'on' and duration:
            dict_vars['message'] += f" {duration}초 동안"
        dict_vars['message'] += "."

        output_on_off = threading.Thread(
            target=self.control.output_on_off,
            args=(output_id, state,),
            kwargs={'output_type': 'sec',
                    'amount': duration,
                    'output_channel': channel})
        output_on_off.start()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup