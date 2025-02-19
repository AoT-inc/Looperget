# coding=utf-8
#
#  verification.py - Verify the difference of two measurements are not beyond a threshold
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
from looperget.utils.influx import add_measurements_influxdb

measurements_dict = {
    0: {
        'measurement': '',
        'unit': '',
        'name': 'Verify'
    }
}

FUNCTION_INFORMATION = {
    'function_name_unique': 'VERIFICATION',
    'function_name': '데이터 검증',
    'measurements_dict': measurements_dict,
    'enable_channel_unit_select': True,

    'message': "이 기능 두 개의 측정값을 획득한 후 그 차이를 계산하며, 차이가 설정된 임계값보다 크지 않을 경우 측정값 A를 저장합니다. 이를 통해 한 센서의 측정값을 다른 센서의 측정값과 비교하여 검증할 수 있습니다. 두 센서의 측정값이 일치할 때만 측정값이 저장되므로, 저장된 측정값을 조건부 함수(Conditional Functions) 등에서 활용하여 측정값이 없는 경우 사용자에게 알림을 보내 센서에 문제가 있을 가능성을 알릴 수 있습니다.",

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
            'name': '{} A'.format(lazy_gettext("Measurement")),
            'phrase': 'Measurement A'
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
            'name': '{} B'.format(lazy_gettext("Measurement")),
            'phrase': 'Measurement B'
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
            'id': 'max_difference',
            'type': 'float',
            'default_value': 10.0,
            'required': True,
            'name': 'Maximum Difference',
            'phrase': 'The maximum allowed difference between the measurements'
        },
        {
            'id': 'average_measurements',
            'type': 'bool',
            'default_value': False,
            'required': True,
            'name': 'Average Measurements',
            'phrase': "Store the average of the measurements in the database"
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
        self.max_difference = None
        self.average_measurements = None

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
            "{}, {}, {}, {}, {}, {}, {}".format(
                self.select_measurement_a_device_id,
                self.select_measurement_a_measurement_id,
                self.measurement_max_age_a,
                self.select_measurement_a_device_id,
                self.select_measurement_a_measurement_id,
                self.measurement_max_age_a,
                self.max_difference))

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
            list_measures = [last_measurement_a[1], last_measurement_b[1]]
            difference = max(list_measures) - min(list_measures)
            if difference > self.max_difference:
                self.logger.debug(
                    "Measurement difference ({}) greater than max allowed ({}). "
                    "Not storing measurement.".format(difference, self.max_difference))
                return

            if self.average_measurements:
                store_value = (last_measurement_a[1] + last_measurement_b[1]) / 2
            else:
                store_value = last_measurement_a[1]

            measurement_dict = {
                0: {
                    'measurement': self.channels_measurement[0].measurement,
                    'unit': self.channels_measurement[0].unit,
                    'value': store_value
                }
            }

            if measurement_dict:
                self.logger.debug(
                    "Adding measurements to InfluxDB with ID {}: {}".format(
                        self.unique_id, measurement_dict))
                add_measurements_influxdb(self.unique_id, measurement_dict)
            else:
                self.logger.debug(
                    "No measurements to add to InfluxDB with ID {}".format(
                        self.unique_id))
