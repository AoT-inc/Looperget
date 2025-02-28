# coding=utf-8
import threading
import time

from flask_babel import lazy_gettext

from looperget.config_translations import TRANSLATIONS
from looperget.databases.models import Actions
from looperget.databases.models import Output
from looperget.actions.base_action import AbstractFunctionAction
from looperget.utils.constraints_pass import constraints_pass_positive_or_zero_value
from looperget.utils.constraints_pass import constraints_pass_positive_value
from looperget.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'output_ramp_pwm',
    'name': f"{TRANSLATIONS['output']['title']}: {TRANSLATIONS['ramp']['title']} {TRANSLATIONS['duty_cycle']['title']}",
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('일정 시간 동안 PWM 출력의 작동 비율을 한 값에서 다른 값으로 점진적으로 변경합니다.'),

    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 설정에 따라 PWM 출력의 작동 비율이 점진적으로 변경됩니다. '
             '<strong>self.run_action("ACTION_ID", value={"output_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "channel": 0, "start": 42, "end": 62, "increment": 1.0, "duration": 600})</strong>를 실행하면 지정된 ID와 채널의 PWM 출력의 작동 비율이 변경됩니다. 시스템에 존재하는 실제 Output ID로 output_id 값을 변경하는 것을 잊지 마십시오.',

    'custom_options': [
        {
            'id': 'output',
            'type': 'select_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels',
            ],
            'name': '출력',
            'phrase': '제어할 출력을 선택하세요'
        },
        {
            'id': 'start',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': "{}: {}".format(lazy_gettext('작동 비율'), lazy_gettext('시작')),
            'phrase': lazy_gettext('PWM의 작동 비율 (백분율, 0.0 - 100.0)')
        },
        {
            'id': 'end',
            'type': 'float',
            'default_value': 50.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': "{}: {}".format(lazy_gettext('작동 비율'), lazy_gettext('종료')),
            'phrase': lazy_gettext('PWM의 작동 비율 (백분율, 0.0 - 100.0)')
        },
        {
            'id': 'increment',
            'type': 'float',
            'default_value': 1.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{} ({})".format(lazy_gettext('증가량'), lazy_gettext('작동 비율')),
            'phrase': '매 지속 시간마다 작동 비율을 얼마나 변경할지 지정합니다.'
        },
        {
            'id': 'duration',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': "{} ({})".format(lazy_gettext('지속 시간'), lazy_gettext('초')),
            'phrase': '시작부터 종료까지 변경하는 데 걸리는 시간(초)을 지정합니다.'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """함수 동작: PWM 출력 작동 비율 점진 변경."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.output_device_id = None
        self.output_channel_id = None
        self.start = None
        self.end = None
        self.increment = None
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
            start = dict_vars["value"]["start"]
        except:
            start = self.start

        try:
            end = dict_vars["value"]["end"]
        except:
            end = self.end

        try:
            increment = dict_vars["value"]["increment"]
        except:
            increment = self.increment

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

        dict_vars['message'] += f"출력 {output_id} CH{channel} ({output.name})의 작동 비율을 {start}%에서 {end}%로, 증가량 {increment}씩, {duration}초 동안 변경합니다."

        change_in_duty_cycle = abs(start - end)
        steps = change_in_duty_cycle * 1 / increment
        seconds_per_step = duration / steps

        current_duty_cycle = start

        output_on = threading.Thread(
            target=self.control.output_on,
            args=(output_id,),
            kwargs={'output_type': 'pwm',
                    'amount': start,
                    'output_channel': channel})
        output_on.start()

        loop_running = True
        timer = time.time() + seconds_per_step
        while True:
            if timer < time.time():
                while timer < time.time():
                    timer += seconds_per_step
                    if start < end:
                        current_duty_cycle += increment
                        if current_duty_cycle > end:
                            current_duty_cycle = end
                            loop_running = False
                    else:
                        current_duty_cycle -= increment
                        if current_duty_cycle < end:
                            current_duty_cycle = end
                            loop_running = False

                output_on = threading.Thread(
                    target=self.control.output_on,
                    args=(output_id,),
                    kwargs={'output_type': 'pwm',
                            'amount': current_duty_cycle,
                            'output_channel': channel})
                output_on.start()

                if not loop_running:
                    break

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup