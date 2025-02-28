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
    'name_unique': 'setpoint_pid_raise',
    'name': "{}: {}: {}".format(TRANSLATIONS['pid']['title'], lazy_gettext('올리기'), lazy_gettext("설정점")),
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('PID의 설정점을 올립니다.'),

    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 선택한 PID 컨트롤러의 설정점이 올려집니다. '
             '<strong>self.run_action("ACTION_ID", value={"pid_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "amount": 2})</strong>를 실행하면 지정된 ID의 PID 컨트롤러의 설정점이 올려집니다. 시스템에 존재하는 실제 PID ID로 pid_id 값을 변경하는 것을 잊지 마십시오.',

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'PID'
            ],
            'name': lazy_gettext('컨트롤러'),
            'phrase': '설정점을 올릴 PID 컨트롤러를 선택하세요'
        },
        {
            'id': 'amount',
            'type': 'float',
            'default_value': 0.0,
            'required': False,
            'name': lazy_gettext('설정점 올리기'),
            'phrase': 'PID 설정점을 올릴 값을 입력하세요'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """함수 동작: PID 설정점 올리기."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.controller_id = None
        self.amount = None

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
            amount = dict_vars["value"]["amount"]
        except:
            amount = self.amount

        pid = db_retrieve_table_daemon(
            PID, unique_id=controller_id, entry='first')

        if not pid:
            msg = f"오류: PID 컨트롤러 ID '{controller_id}'를 찾을 수 없습니다."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        new_setpoint = pid.setpoint + amount
        dict_vars['message'] += f"PID {controller_id} ({pid.name})의 설정점을 {amount}만큼 올려 {new_setpoint}(으)로 변경합니다."

        if pid.is_activated:
            setpoint_pid = threading.Thread(
                target=self.control.pid_set,
                args=(pid.unique_id,
                      'setpoint',
                      new_setpoint,))
            setpoint_pid.start()
        else:
            with session_scope(LOOPERGET_DB_PATH) as new_session:
                mod_pid = new_session.query(PID).filter(
                    PID.unique_id == controller_id).first()
                mod_pid.setpoint = new_setpoint
                new_session.commit()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup