# coding=utf-8
#
#  bang_bang_on_off.py - A hysteretic control for On/Off Outputs
import time

from flask_babel import lazy_gettext

from looperget.databases.models import CustomController
from looperget.functions.base_function import AbstractFunction
from looperget.looperget_client import DaemonControl
from looperget.utils.constraints_pass import constraints_pass_positive_value
from looperget.utils.database import db_retrieve_table_daemon


FUNCTION_INFORMATION = {
    'function_name_unique': 'bang_bang_on_off',
    'function_name': '뱅-뱅 히스테릭 (On/Off) (Raise/Lower/Both)',
    'function_name_short': 'Bang-Bang (On/Off, Raise/Lower/Both)',

    'message': '단순한 Bang-Bang 제어 방식으로, 하나의 입력값을 사용하여 하나 또는 두 개의 출력을 제어합니다.'
               '입력을 선택하고, 증가(Raise) 및/또는 감소(Lower) 출력을 설정한 후, **설정값(Setpoint)과 히스테리시스(Hysteresis: 작동 범위)를 입력하고 방향(Direction)을 선택하세요.'
               '    •	Raise 모드 (예: 난방): 입력값이 (설정값 - 히스테리시스) 이하일 때 출력이 켜짐, 입력값이 (설정값 + 히스테리시스) 이상일 때 출력이 꺼짐'
               '    •	Lower 모드 (예: 냉각): 위 동작과 반대로, 입력값을 낮추기 위해 출력을 켜려 함'
               '    •	Both: 입력값이 설정값을 유지하도록 Raise 및 Lower를 조정',

    'options_disabled': [
        'measurements_select',
        'measurements_configure'
    ],

    'custom_options': [
        {
            'id': 'measurement',
            'type': 'select_measurement',
            'default_value': '',
            'required': True,
            'options_select': [
                'Input',
                'Function'
            ],
            'name': lazy_gettext('Measurement'),
            'phrase': lazy_gettext('Select a measurement the selected output will affect')
        },
        {
            'id': 'measurement_max_age',
            'type': 'integer',
            'default_value': 360,
            'required': True,
            'name': "{}: {} ({})".format(lazy_gettext("Measurement"), lazy_gettext("Max Age"),
                                         lazy_gettext("Seconds")),
            'phrase': lazy_gettext('The maximum age of the measurement to use')
        },
        {
            'id': 'output_raise',
            'type': 'select_measurement_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels_Measurements',
            ],
            'name': 'Output (Raise)',
            'phrase': 'Select an output to control that will raise the measurement'
        },
        {
            'id': 'output_lower',
            'type': 'select_measurement_channel',
            'default_value': '',
            'required': True,
            'options_select': [
                'Output_Channels_Measurements',
            ],
            'name': 'Output (Lower)',
            'phrase': 'Select an output to control that will lower the measurement'
        },
        {
            'id': 'setpoint',
            'type': 'float',
            'default_value': 50,
            'required': True,
            'name': lazy_gettext('Setpoint'),
            'phrase': lazy_gettext('The desired setpoint')
        },
        {
            'id': 'hysteresis',
            'type': 'float',
            'default_value': 1,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Hysteresis'),
            'phrase': lazy_gettext('The amount above and below the setpoint that defines the control band')
        },
        {
            'id': 'direction',
            'type': 'select',
            'default_value': 'both',
            'required': True,
            'options_select': [
                ('raise', 'Raise'),
                ('lower', 'Lower'),
                ('both', 'Both')
            ],
            'name': lazy_gettext('Direction'),
            'phrase': 'Raise means the measurement will increase when the control is on (heating). Lower means the measurement will decrease when the output is on (cooling)'
        },
        {
            'id': 'update_period',
            'type': 'float',
            'default_value': 5,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{} ({})".format(lazy_gettext('Period'), lazy_gettext('Seconds')),
            'phrase': lazy_gettext('The duration between measurements or actions')
        }
    ]
}


class CustomModule(AbstractFunction):
    """
    Class to operate custom controller
    """
    def __init__(self, function, testing=False):
        super().__init__(function, testing=testing, name=__name__)

        self.control_variable = None
        self.control = DaemonControl()
        self.timer_loop = time.time()

        # Initialize custom options
        self.measurement_device_id = None
        self.measurement_measurement_id = None
        self.measurement_max_age = None
        self.output_raise_device_id = None
        self.output_raise_measurement_id = None
        self.output_raise_channel_id = None
        self.output_lower_device_id = None
        self.output_lower_measurement_id = None
        self.output_lower_channel_id = None
        self.setpoint = None
        self.hysteresis = None
        self.direction = None
        self.output_raise_channel = None
        self.output_lower_channel = None
        self.update_period = None

        # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.output_raise_channel = self.get_output_channel_from_channel_id(
            self.output_raise_channel_id)
        self.output_lower_channel = self.get_output_channel_from_channel_id(
            self.output_lower_channel_id)

        self.logger.info(
            "Bang-Bang controller started with options: "
            "Measurement Device: {}, Measurement: {}, "
            "Output Raise: {}, Output_Raise_Channel: {}, "
            "Output Lower: {}, Output_Lower_Channel: {}, "
            "Setpoint: {}, Hysteresis: {}, "
            "Direction: {}, Period: {}".format(
                self.measurement_device_id,
                self.measurement_measurement_id,
                self.output_raise_device_id,
                self.output_raise_channel,
                self.output_lower_device_id,
                self.output_lower_channel,
                self.setpoint,
                self.hysteresis,
                self.direction,
                self.update_period))

    def loop(self):
        if self.timer_loop > time.time():
            return

        while self.timer_loop < time.time():
            self.timer_loop += self.update_period

        if ((self.direction == 'raise' and self.output_raise_channel is None) or
                (self.direction == 'lower' and self.output_lower_channel is None) or
                self.direction == 'both' and None in [self.output_raise_channel, self.output_lower_channel]):
            self.logger.error("Cannot start bang-bang controller: Check output channel(s).")
            return

        last_measurement = self.get_last_measurement(
            self.measurement_device_id,
            self.measurement_measurement_id,
            max_age=self.measurement_max_age)

        if not last_measurement:
            self.logger.error("Could not acquire a measurement")
            return

        if self.direction == 'raise':
            if last_measurement[1] > (self.setpoint + self.hysteresis):
                self.logger.debug("Raise: Off")
                self.control.output_off(
                    self.output_raise_device_id, output_channel=self.output_raise_channel)
            elif last_measurement[1] < (self.setpoint - self.hysteresis):
                self.logger.debug("Raise: On")
                self.control.output_on(
                    self.output_raise_device_id, output_channel=self.output_raise_channel)

        elif self.direction == 'lower':
            if last_measurement[1] < (self.setpoint - self.hysteresis):
                self.logger.debug("Lower: Off")
                self.control.output_off(
                    self.output_lower_device_id, output_channel=self.output_lower_channel)
            elif last_measurement[1] > (self.setpoint + self.hysteresis):
                self.logger.debug("Lower: On")
                self.control.output_on(
                    self.output_lower_device_id, output_channel=self.output_lower_channel)

        elif self.direction == 'both':
            if (self.setpoint - self.hysteresis) < last_measurement[1] < (self.setpoint + self.hysteresis):
                self.logger.debug("Lower: Off, Raise: Off")
                self.control.output_off(
                    self.output_raise_device_id, output_channel=self.output_raise_channel)
                self.control.output_off(
                    self.output_lower_device_id, output_channel=self.output_lower_channel)

            elif last_measurement[1] > (self.setpoint + self.hysteresis):
                self.logger.debug("Lower: On, Raise: Off")
                self.control.output_off(
                    self.output_raise_device_id, output_channel=self.output_raise_channel)
                self.control.output_on(
                    self.output_lower_device_id, output_channel=self.output_lower_channel)

            elif last_measurement[1] < (self.setpoint - self.hysteresis):
                self.logger.debug("Lower: Off, Raise: On")
                self.control.output_off(
                    self.output_lower_device_id, output_channel=self.output_lower_channel)
                self.control.output_on(
                    self.output_raise_device_id, output_channel=self.output_raise_channel)
        else:
            self.logger.error(
                "Unknown controller direction: '{}'".format(self.direction))

        output_raise_state = self.control.output_state(
            self.output_raise_device_id, self.output_raise_channel)
        output_lower_state = self.control.output_state(
            self.output_lower_device_id, self.output_lower_channel)

        self.logger.debug(
            f"Before execution: Input: {last_measurement[1]}, "
            f"output_raise: {output_raise_state}, "
            f"output_lower: {output_lower_state}, "
            f"target: {self.setpoint}, "
            f"hyst: {self.hysteresis}")

    def stop_function(self):
        self.control.output_off(
            self.output_raise_device_id, output_channel=self.output_raise_channel)
        self.control.output_off(
            self.output_lower_device_id, output_channel=self.output_lower_channel)
