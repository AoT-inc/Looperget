# coding=utf-8
import copy

from looperget.inputs.base_input import AbstractInput
from looperget.looperget_client import DaemonControl

# Measurements
measurements_dict = {
    0: {
        'measurement': 'disk_space',
        'unit': 'MB',
        'name': 'System RAM Free'
    },
    1: {
        'measurement': 'disk_space',
        'unit': 'MB',
        'name': 'System RAM Used'
    },
    2: {
        'measurement': 'disk_space',
        'unit': 'MB',
        'name': 'Looperget Backend RAM Used'
    },
    3: {
        'measurement': 'disk_space',
        'unit': 'MB',
        'name': 'Looperget Frontend RAM Used'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name': 'System and Looperget RAM',
    'input_name_unique': 'LOOPERGET_RAM',
    'input_manufacturer': 'Looperget',
    'input_library': 'psutil, resource.getrusage()',
    'measurements_name': 'RAM Allocation',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'period',
        'measurements_select'
    ],

    'dependencies_module': [
        ('pip-pypi', 'psutil', 'psutil==5.9.4')
    ],

    'custom_options': [
        {
            'id': 'endpoint_frontend_ram',
            'type': 'text',
            'default_value': 'https://127.0.0.1/ram',
            'required': False,
            'name': 'Looperget Frontend RAM Endpoint',
            'phrase': 'The endpoint to get Looperget frontend ram usage'
        }
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures ram used by the Looperget daemon
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.control = None

        self.endpoint_frontend_ram = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        self.control = DaemonControl()

    def get_measurement(self):
        """Gets the measurement in units by reading resource."""
        self.return_dict = copy.deepcopy(measurements_dict)

        import psutil

        try:
            system = psutil.virtual_memory()
            if self.is_enabled(0):
                self.value_set(0, system.available / (1024.0 ** 2))
            if self.is_enabled(1):
                self.value_set(1, system.used / (1024.0 ** 2))
        except:
            self.logger.exception("getting system ram")

        if self.is_enabled(2):
            self.value_set(2, self.control.ram_use())

        if self.is_enabled(3):
            try:
                import requests
                response = requests.get(self.endpoint_frontend_ram, verify=False)
                self.value_set(3, float(response.content))
            except:
                self.logger.exception("getting frontend ram usage")

        return self.return_dict
