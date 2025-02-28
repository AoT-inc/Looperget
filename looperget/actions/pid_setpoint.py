# coding=utf-8
import threading

from flask_babel import lazy_gettext

from looperget.actions.base_action import AbstractFunctionAction
from looperget.config import LOOPERGET_DB_PATH
from looperget.config_translations import TRANSLATIONS
from looperget.databases.models import Actions
from looperget.databases.models import PID
from looperget.databases.utils import session_scope
from looperget.utils.database import db_retrieve_table_daemon


ACTION_INFORMATION = {
    'name_unique': 'setpoint_pid',
    'name': "{}: {}: {}".format(TRANSLATIONS['pid']['title'], lazy_gettext('설정'), lazy_gettext("설정점")),
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('PID의 설정점을 설정합니다.'),

    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 선택한 PID 컨트롤러의 설정점을 설정합니다. '
             '<strong>self.run_action("ACTION_ID", value={"setpoint": 42})</strong>를 실행하면 PID 컨트롤러의 설정점이 (예: 42)로 설정됩니다. '
             '또한 PID ID를 지정할 수도 있습니다 (예: value={"setpoint": 42, "pid_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"}). '
             '시스템에 존재하는 실제 PID ID로 pid_id 값을 변경하는 것을 잊지 마십시오.',

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'PID'
            ],
            'name': lazy_gettext('컨트롤러'),
            'phrase': 'PID 컨트롤러를 선택하세요'
        },
        {
            'id': 'setpoint',
            'type': 'float',
            'default_value': 0.0,
            'required': False,
            'name': lazy_gettext('설정점'),
            'phrase': 'PID 컨트롤러의 설정점을 입력하세요'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: PID Setpoint Set."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.controller_id = None
        self.setpoint = None

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
            setpoint = dict_vars["value"]["setpoint"]
        except:
            setpoint = self.setpoint

        pid = db_retrieve_table_daemon(
            PID, unique_id=controller_id, entry='first')

        if not pid:
            msg = f" 오류: PID 컨트롤러 ID '{controller_id}'를 찾을 수 없습니다."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        dict_vars['message'] += f" PID {controller_id} ({pid.name})의 설정점을 설정합니다."

        if pid.is_activated:
            setpoint_pid = threading.Thread(
                target=self.control.pid_set,
                args=(pid.unique_id,
                      'setpoint',
                      setpoint,))
            setpoint_pid.start()
        else:
            with session_scope(LOOPERGET_DB_PATH) as new_session:
                mod_pid = new_session.query(PID).filter(
                    PID.unique_id == controller_id).first()
                mod_pid.setpoint = setpoint
                new_session.commit()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup