# coding=utf-8
#
#  sum_last_multiple.py - Calculates the sum of last measurements for multiple channels
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

from looperget.databases.models import Conversion
from looperget.databases.models import CustomController
from looperget.functions.base_function import AbstractFunction
from looperget.looperget_client import DaemonControl
from looperget.utils.constraints_pass import constraints_pass_positive_value
from looperget.utils.database import db_retrieve_table_daemon
from looperget.utils.influx import add_measurements_influxdb
from looperget.utils.influx import read_influxdb_single
from looperget.utils.system_pi import get_measurement
from looperget.utils.system_pi import return_measurement_info

measurements_dict = {
    0: {
        'measurement': '',
        'unit': '',
        'name': 'Sum'
    }
}

FUNCTION_INFORMATION = {
    'function_name_unique': 'SUM_LAST_MULTI',
    'function_name': '합계 (Last, Multiple)',
    'measurements_dict': measurements_dict,
    'enable_channel_unit_select': True,

    'message': '이 기능은 선택된 측정값 중 마지막 값을 가져와 합산한 후, 결과값을 선택된 측정값과 단위로 저장합니다.',

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
            'id': 'start_offset',
            'type': 'integer',
            'default_value': 10,
            'required': True,
            'name': "{} ({})".format(lazy_gettext('Start Offset'), lazy_gettext('Seconds')),
            'phrase': lazy_gettext('The duration to wait before the first operation')
        },
        {
            'id': 'max_measure_age',
            'type': 'integer',
            'default_value': 360,
            'required': True,
            'name': "{} ({})".format(lazy_gettext('Max Age'), lazy_gettext('Seconds')),
            'phrase': lazy_gettext('The maximum age of the measurement to use')
        },
        {
            'id': 'select_measurement',
            'type': 'select_multi_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Function',
                'Output'
            ],
            'name': 'Measurement',
            'phrase': 'Measurement to replace "x" in the equation'
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
        self.start_offset = None
        self.select_measurement = None
        self.max_measure_age = None

        # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.timer_loop = time.time() + self.start_offset

    def loop(self):
        if self.timer_loop > time.time():
            return

        while self.timer_loop < time.time():
            self.timer_loop += self.period

        measurements = []
        for each_id_set in self.select_measurement:
            device_device_id = each_id_set.split(",")[0]
            device_measure_id = each_id_set.split(",")[1]

            device_measurement = get_measurement(device_measure_id)

            if not device_measurement:
                self.logger.error("Could not find Device Measurement")
                return

            conversion = db_retrieve_table_daemon(
                Conversion, unique_id=device_measurement.conversion_id)
            channel, unit, measurement = return_measurement_info(
                device_measurement, conversion)

            last_measurement = read_influxdb_single(
                device_device_id,
                unit,
                channel,
                measure=measurement,
                duration_sec=self.max_measure_age,
                value='LAST')

            if not last_measurement:
                self.logger.error("Could not find measurement within the set Max Age")
                return False
            else:
                measurements.append(last_measurement[1])

        sum_measurements = float(sum(measurements))

        measurement_dict = {
            0: {
                'measurement': self.channels_measurement[0].measurement,
                'unit': self.channels_measurement[0].unit,
                'value': sum_measurements
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
