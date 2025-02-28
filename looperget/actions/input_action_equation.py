# coding=utf-8
from flask_babel import lazy_gettext

from looperget.actions.base_action import AbstractFunctionAction
from looperget.databases.models import Actions
from looperget.utils.database import db_retrieve_table_daemon
from looperget.utils.system_pi import get_measurement

ACTION_INFORMATION = {
    'name_unique': 'input_action_equation',
    'name': "{} (Single-Measurement)".format(lazy_gettext('방정식')),
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['inputs'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': '데이터베이스에 저장하기 전에 방정식을 사용하여 채널 값을 수정합니다.',

    'usage': '',

    'custom_options': [
        {
            'id': 'measurement',
            'type': 'select_measurement_from_this_input',
            'default_value': None,
            'name': lazy_gettext('측정'),
            'phrase': '페이로드로 전송할 측정을 선택하세요'
        },
        {
            'id': 'equation',
            'type': 'text',
            'default_value': 'x-10',
            'required': True,
            'name': lazy_gettext('방정식'),
            'phrase': '값을 저장하기 전에 적용할 방정식입니다. "x"는 측정값을 의미합니다. 예: x-10'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Equation."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.measurement_device_id = None
        self.measurement_measurement_id = None
        self.equation = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.action_setup = True

    def run_action(self, dict_vars):
        device_measurement = get_measurement(
            self.measurement_measurement_id)

        if not device_measurement:
            msg = f"오류: 페이로드로 사용할 측정값이 선택되어야 합니다."
            self.logger.error(msg)
            dict_vars['message'] += msg
            return dict_vars

        channel = device_measurement.channel

        try:
            original_value = dict_vars['measurements_dict'][channel]['value']
        except:
            original_value = None

        if original_value is None:
            msg = f"오류: 채널 {channel}에 대해 액션에 전달된 딕셔너리에서 측정값을 찾을 수 없습니다."
            self.logger.debug(msg)
            dict_vars['message'] += msg
            return dict_vars

        equation_str = self.equation
        equation_str = equation_str.replace("x", str(original_value))

        self.logger.debug("Equation: {} = {}".format(self.equation, equation_str))

        dict_vars['measurements_dict'][channel]['value'] = eval(equation_str)

        self.logger.debug(
            f"Input channel: {channel}, "
            f"original value: {original_value}, "
            f"returned value: {dict_vars['measurements_dict'][channel]['value']}")

        dict_vars['message'] += f" 방정식 '{equation_str}', 반환값 = {dict_vars['measurements_dict'][channel]['value']}."

        return dict_vars

    def is_setup(self):
        return self.action_setup