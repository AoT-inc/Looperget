# coding=utf-8
#
#  difference.py - Calculate difference between two measurements
#
#  Copyright (C) 2015-2020 Kyle T. Gabriel <looperget@aot-inc.com>
#
#  This file is part of Looperget
#
#  Looperget is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Looperget is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Looperget. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at aot-inc.com
#
import time

from flask_babel import lazy_gettext

from looperget.databases.models import CustomController
from looperget.functions.base_function import AbstractFunction
from looperget.looperget_client import DaemonControl
from looperget.utils.constraints_pass import constraints_pass_positive_value
from looperget.utils.database import db_retrieve_table_daemon
from looperget.utils.influx import write_influxdb_value

measurements_dict = {
    0: {
        'measurement': '',
        'unit': '',
        'name': 'Difference'
    }
}

FUNCTION_INFORMATION = {
    'function_name_unique': 'DIFFERENCE',
    'function_name': '차이 측정',
    'measurements_dict': measurements_dict,
    'enable_channel_unit_select': True,

    'message': '이 함수는 두 개의 측정값을 가져와 차이를 계산한 후, 결과값을 선택된 측정값과 단위로 저장합니다.',

    'options_enabled': [
        'measurements_select_measurement_unit',
        'custom_options'
    ],

    'custom_options': [
        {
            'id': 'period',
            'type': 'float',
            'default_value': 60,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{} ({})".format(lazy_gettext('Period'), lazy_gettext('Seconds')),
            'phrase': lazy_gettext('The duration between measurements or actions')
        },
        {
            'id': 'select_measurement_a',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Function'
            ],
            'name': '{}: A'.format(lazy_gettext("Measurement")),
            'phrase': ''
        },
        {
            'id': 'measurement_max_age_a',
            'type': 'integer',
            'default_value': 360,
            'required': True,
            'name': "{} A: {} ({})".format(lazy_gettext("Measurement"), lazy_gettext("Max Age"), lazy_gettext("Seconds")),
            'phrase': lazy_gettext('The maximum age of the measurement to use')
        },
        {
            'id': 'select_measurement_b',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Function'
            ],
            'name': '{}: B'.format(lazy_gettext("Measurement")),
            'phrase': ''
        },
        {
            'id': 'measurement_max_age_b',
            'type': 'integer',
            'default_value': 360,
            'required': True,
            'name': "{} B: {} ({})".format(lazy_gettext("Measurement"), lazy_gettext("Max Age"), lazy_gettext("Seconds")),
            'phrase': lazy_gettext('The maximum age of the measurement to use')
        },
        {
            'id': 'difference_reverse_order',
            'type': 'bool',
            'default_value': False,
            'required': True,
            'name': 'Reverse Order',
            'phrase': 'Reverse the order in the calculation'
        },
        {
            'id': 'difference_absolute',
            'type': 'bool',
            'default_value': False,
            'required': True,
            'name': 'Absolute Difference',
            'phrase': 'Return the absolute value of the difference'
        }
    ]
}


class CustomModule(AbstractFunction):
    """
    Class to operate custom controller
    """
    def __init__(self, function, testing=False):
        super().__init__(function, testing=testing, name=__name__)

        self.timer_loop = time.time()

        self.control = DaemonControl()

        # Initialize custom options
        self.period = None
        self.select_measurement_a_device_id = None
        self.select_measurement_a_measurement_id = None
        self.measurement_max_age_a = None
        self.select_measurement_b_device_id = None
        self.select_measurement_b_measurement_id = None
        self.measurement_max_age_b = None
        self.difference_reverse_order = None
        self.difference_absolute = None

        # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.logger.debug(
            "Custom controller started with options: "
            "{}, {}, {}, {}, {}, {}".format(
                self.select_measurement_a_device_id,
                self.select_measurement_a_measurement_id,
                self.measurement_max_age_a,
                self.select_measurement_a_device_id,
                self.select_measurement_a_measurement_id,
                self.measurement_max_age_a))

    def loop(self):
        if self.timer_loop > time.time():
            return

        while self.timer_loop < time.time():
            self.timer_loop += self.period

        last_measurement_a = self.get_last_measurement(
            self.select_measurement_a_device_id,
            self.select_measurement_a_measurement_id,
            max_age=self.measurement_max_age_a)

        if last_measurement_a:
            self.logger.debug(
                "Most recent timestamp and measurement for "
                "Measurement A: {timestamp}, {meas}".format(
                    timestamp=last_measurement_a[0],
                    meas=last_measurement_a[1]))
        else:
            self.logger.debug(
                "Could not find a measurement in the database for "
                "Measurement A in the past {} seconds".format(
                    self.measurement_max_age_a))

        last_measurement_b = self.get_last_measurement(
            self.select_measurement_b_device_id,
            self.select_measurement_b_measurement_id,
            max_age=self.measurement_max_age_b)

        if last_measurement_b:
            self.logger.debug(
                "Most recent timestamp and measurement for "
                "Measurement B: {timestamp}, {meas}".format(
                    timestamp=last_measurement_b[0],
                    meas=last_measurement_b[1]))
        else:
            self.logger.debug(
                "Could not find a measurement in the database for "
                "Measurement B in the past {} seconds".format(
                    self.measurement_max_age_b))

        if last_measurement_a and last_measurement_b:
            if self.difference_reverse_order:
                difference = last_measurement_b[1] - last_measurement_a[1]
            else:
                difference = last_measurement_a[1] - last_measurement_b[1]
            if self.difference_absolute:
                difference = abs(difference)

            self.logger.debug("Output: {}".format(difference))

            write_influxdb_value(
                self.unique_id,
                self.channels_measurement[0].unit,
                value=difference,
                measure=self.channels_measurement[0].measurement,
                channel=0)
