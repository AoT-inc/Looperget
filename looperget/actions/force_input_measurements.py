# coding=utf-8
import threading

from flask_babel import lazy_gettext

from looperget.actions.base_action import AbstractFunctionAction
from looperget.databases.models import Actions
from looperget.databases.models import Input
from looperget.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'input_force_measurements',
    'name': "{}: {}:".format(lazy_gettext('입력'), lazy_gettext('강제 측정')),
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('입력에 대해 강제 측정을 수행합니다.'),

    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 선택된 입력에 대해 강제 측정을 수행합니다. '
             '<strong>self.run_action("ACTION_ID", value={"input_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong>를 실행하면 지정된 ID를 가진 입력에 대해 강제 측정을 수행합니다. 시스템에 존재하는 실제 입력 ID로 input_id 값을 변경하는 것을 잊지 마십시오.',

    'custom_options': [
        {
            'id': 'input',
            'type': 'select_device',
            'default_value': '',
            'required': False,
            'options_select': [
                '입력'
            ],
            'name': '입력',
            'phrase': '입력을 선택하세요'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Force Input Measurements."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.input_id = None

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
            input_id = dict_vars["value"]["input_id"]
        except:
            input_id = self.input_id

        this_input = db_retrieve_table_daemon(
            Input, unique_id=input_id, entry='first')

        if not this_input:
            msg = f"ID {input_id}에 해당하는 입력을 찾을 수 없습니다."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        dict_vars['message'] += f" 입력 {input_id} ({this_input.name})에 대해 강제 측정을 수행합니다."

        force_measurements = threading.Thread(
            target=self.control.input_force_measurements,
            args=(input_id,))
        force_measurements.start()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup