# coding=utf-8
#
#  statistics_last_multiple.py - Calculate statistics for multiple measurements
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
from statistics import median
from statistics import stdev

from flask_babel import lazy_gettext

from looperget.databases.models import Conversion
from looperget.databases.models import CustomController
from looperget.functions.base_function import AbstractFunction
from looperget.looperget_client import DaemonControl
from looperget.utils.constraints_pass import constraints_pass_positive_value
from looperget.utils.database import db_retrieve_table_daemon
from looperget.utils.influx import read_influxdb_single
from looperget.utils.influx import write_influxdb_value
from looperget.utils.system_pi import get_measurement
from looperget.utils.system_pi import return_measurement_info

measurements_dict = {
    0: {
        'measurement': '',
        'unit': '',
        'name': 'Mean'
    },
    1: {
        'measurement': '',
        'unit': '',
        'name': 'Median'
    },
    2: {
        'measurement': '',
        'unit': '',
        'name': 'Minimum'
    },
    3: {
        'measurement': '',
        'unit': '',
        'name': 'Maximum'
    },
    4: {
        'measurement': '',
        'unit': '',
        'name': 'Standard Deviation'
    },
    5: {
        'measurement': '',
        'unit': '',
        'name': 'St. Dev. of Mean (upper)'
    },
    6: {
        'measurement': '',
        'unit': '',
        'name': 'St. Dev. of Mean (lower)'
    }
}

FUNCTION_INFORMATION = {
    'function_name_unique': 'STAT_LAST_MULTI',
    'function_name': '통계 (Last, Multiple)',
    'measurements_dict': measurements_dict,
    'enable_channel_unit_select': True,

    'message': '이 기능은 여러 개의 측정값을 가져와 통계를 계산한 후, 결과값을 선택된 단위로 저장합니다.',

    'options_enabled': [
        'measurements_select_measurement_unit',
        'measurements_select',
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
                'Function'
            ],
            'name': 'Measurement',
            'phrase': 'Measurements to perform statistics on'
        },
        {
            'id': 'halt_on_missing_measure',
            'type': 'bool',
            'default_value': False,
            'required': True,
            'name': 'Halt on Missing Measurement',
            'phrase': "Don't calculate statistics if >= 1 measurement is not found within Max Age"
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
        self.select_measurement = None
        self.max_measure_age = None
        self.halt_on_missing_measure = None

        # Set custom options
        custom_function = db_retrieve_table_daemon(
            CustomController, unique_id=self.unique_id)
        self.setup_custom_options(
            FUNCTION_INFORMATION['custom_options'], custom_function)

    def loop(self):
        if self.timer_loop > time.time():
            return

        while self.timer_loop < time.time():
            self.timer_loop += self.period

        measure = []
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
                self.logger.error(
                    "Could not find measurement within the set Max Age for Device {} and Measurement {}".format(
                        device_device_id, device_measure_id))
                if self.halt_on_missing_measure:
                    self.logger.debug("Instructed to halt on the first missing measurement. Halting.")
                    return False
            else:
                measure.append(last_measurement[1])

        if len(measure) > 1:
            stat_mean = float(sum(measure) / float(len(measure)))
            stat_median = median(measure)
            stat_minimum = min(measure)
            stat_maximum = max(measure)
            stdev_ = stdev(measure)
            stdev_mean_upper = stat_mean + stdev_
            stdev_mean_lower = stat_mean - stdev_

            list_measurement = [
                stat_mean,
                stat_median,
                stat_minimum,
                stat_maximum,
                stdev_,
                stdev_mean_upper,
                stdev_mean_lower
            ]

            for each_channel, each_measurement in self.channels_measurement.items():
                if each_measurement.is_enabled:
                    channel, unit, measurement = return_measurement_info(
                        each_measurement, self.channels_conversion[each_channel])

                    self.logger.debug("Saving {} to channel {} with measurement {} and unit {}".format(
                        list_measurement[each_channel], each_channel, measurement, unit))

                    write_influxdb_value(
                        self.unique_id,
                        unit,
                        value=list_measurement[each_channel],
                        measure=measurement,
                        channel=each_channel)
        else:
            self.logger.debug("Less than 2 measurements found within Max Age. "
                              "Calculations need at least 2 measurements. Not calculating.")
