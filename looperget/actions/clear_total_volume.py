# coding=utf-8
import threading

from flask_babel import lazy_gettext

from looperget.databases.models import Actions
from looperget.databases.models import Input
from looperget.actions.base_action import AbstractFunctionAction
from looperget.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'clear_total_volume',
    'name': "{}: {} ({})".format(lazy_gettext('유량계'), lazy_gettext('총합 초기화'), lazy_gettext('부피')),
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': '유량계 입력에 저장된 총 부피를 초기화합니다. 해당 입력에는 총 부피 초기화 옵션이 있어야 합니다.',
    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 선택한 유량계 입력의 총 부피가 초기화됩니다. '
             '<strong>self.run_action("ACTION_ID", value={"input_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong>를 실행하면 지정된 ID의 유량계 입력의 총 부피가 초기화됩니다. '
             '시스템에 존재하는 실제 입력 ID로 input_id 값을 변경하는 것을 잊지 마십시오.',
    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Input'
            ],
            'name': lazy_gettext('컨트롤러'),
            'phrase': '유량계 입력을 선택하세요'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Clear Total Volume."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.controller_id = None

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
            controller_id = dict_vars["value"]["input_id"]
        except:
            controller_id = self.controller_id

        this_input = db_retrieve_table_daemon(
            Input, unique_id=controller_id, entry='first')

        if not this_input:
            msg = f"오류: ID '{controller_id}'에 해당하는 입력을 찾을 수 없습니다."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        dict_vars['message'] += f"입력 {controller_id} ({this_input.name})의 총 부피를 초기화합니다."
        clear_volume = threading.Thread(
            target=self.control.module_function,
            args=("Input", this_input.unique_id, "clear_total_volume", {},))
        clear_volume.start()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup