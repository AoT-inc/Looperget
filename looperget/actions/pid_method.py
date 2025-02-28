# coding=utf-8
import threading

from flask_babel import lazy_gettext

from looperget.actions.base_action import AbstractFunctionAction
from looperget.config import LOOPERGET_DB_PATH
from looperget.config_translations import TRANSLATIONS
from looperget.databases.models import Actions
from looperget.databases.models import Method
from looperget.databases.models import PID
from looperget.databases.utils import session_scope
from looperget.utils.database import db_retrieve_table_daemon


ACTION_INFORMATION = {
    'name_unique': 'method_pid',
    'name': "{}: {}".format(TRANSLATIONS['pid']['title'], lazy_gettext('참조궤적 설정')),
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('Select a method to set the PID to use.'),

    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 선택된 PID 컨트롤러가 일시 정지됩니다. '
             '<strong>self.run_action("ACTION_ID", value={"pid_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "method_id": "fe8b8f41-131b-448d-ba7b-00a044d24075"})</strong>를 실행하면 지정된 ID를 가진 PID 컨트롤러에 참조궤적이 설정됩니다. '
             '시스템에 존재하는 실제 PID ID로 pid_id 값을 변경하는 것을 잊지 마십시오.',

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'PID'
            ],
            'name': lazy_gettext('Controller'),
            'phrase': '참조궤적을 적용할 PID 컨트롤러를 선택하세요'
        },
        {
            'id': 'method',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Method'
            ],
            'name': lazy_gettext('Method'),
            'phrase': 'PID에 적용할 참조궤적을 선택하세요'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: PID Set Method."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.controller_id = None
        self.method_id = None

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
            controller_id = dict_vars["value"]["pid_id"]
        except:
            controller_id = self.controller_id

        try:
            method_id = dict_vars["value"]["method_id"]
        except:
            method_id = self.method_id

        pid = db_retrieve_table_daemon(
            PID, unique_id=controller_id, entry='first')

        if not pid:
            msg = f" 오류: ID '{controller_id}'에 해당하는 PID 컨트롤러를 찾을 수 없습니다."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        method = db_retrieve_table_daemon(
            Method, unique_id=method_id, entry='first')

        if not method:
            msg = f" 오류: ID {method_id}에 해당하는 참조궤적을 찾을 수 없습니다."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        dict_vars['message'] += f" PID {controller_id} ({pid.name})에 참조궤적{method_id} ({method.name})가 설정되었습니다."

        if pid.is_activated:
            method_pid = threading.Thread(
                target=self.control.pid_set,
                args=(controller_id,
                      'method',
                      method_id,))
            method_pid.start()
        else:
            with session_scope(LOOPERGET_DB_PATH) as new_session:
                mod_pid = new_session.query(PID).filter(
                    PID.unique_id == controller_id).first()
                mod_pid.method_id = method_id
                new_session.commit()

        self.logger.debug(f"message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup