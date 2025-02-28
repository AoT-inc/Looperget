# coding=utf-8
import threading

from flask_babel import lazy_gettext

from looperget.actions.base_action import AbstractFunctionAction
from looperget.config import LOOPERGET_DB_PATH
from looperget.config_translations import TRANSLATIONS
from looperget.databases.models import Actions
from looperget.databases.utils import session_scope
from looperget.utils.actions import which_controller
from looperget.utils.database import db_retrieve_table_daemon


ACTION_INFORMATION = {
    'name_unique': 'deactivate_controller',
    'name': f"{TRANSLATIONS['controller']['title']}: {TRANSLATIONS['deactivate']['title']}",
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('컨트롤러를 비활성화합니다.'),

    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 선택한 컨트롤러가 비활성화됩니다. '
             '<strong>self.run_action("ACTION_ID", value={"controller_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong>를 실행하면 지정된 ID의 컨트롤러가 비활성화됩니다. '
             '시스템에 존재하는 실제 컨트롤러 ID로 controller_id 값을 변경하는 것을 잊지 마십시오.',

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Input',
                'Math',
                'Function',
                'Conditional',
                'PID',
                'Trigger'
            ],
            'name': lazy_gettext('컨트롤러'),
            'phrase': '비활성화할 컨트롤러를 선택하세요'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Deactivate Controller."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        # Initialize custom options
        self.controller_id = None

        # Set custom options
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
            controller_id = dict_vars["value"]["controller_id"]
        except:
            controller_id = self.controller_id

        self.logger.debug(f"Finding controller with ID {controller_id}")

        (controller_type,
         controller_object,
         controller_entry) = which_controller(controller_id)

        if not controller_entry:
            msg = f"오류: ID '{controller_id}'의 컨트롤러를 찾을 수 없습니다."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        dict_vars['message'] += f"컨트롤러 {controller_id} ({controller_entry.name})를 비활성화합니다."

        if not controller_entry.is_activated:
            dict_vars['message'] += " 알림: 컨트롤러가 이미 비활성화되어 있습니다!"
        else:
            with session_scope(LOOPERGET_DB_PATH) as new_session:
                mod_cont = new_session.query(controller_object).filter(
                    controller_object.unique_id == controller_id).first()
                mod_cont.is_activated = False
                new_session.commit()
            deactivate_controller = threading.Thread(
                target=self.control.controller_deactivate,
                args=(controller_id,))
            deactivate_controller.start()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup