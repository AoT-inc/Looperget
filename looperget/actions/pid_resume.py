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
    'name_unique': 'resume_pid',
    'name': f"{TRANSLATIONS['pid']['title']}: {TRANSLATIONS['resume']['title']}",
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('PID를 재개합니다.'),

    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 선택한 PID 컨트롤러가 재개됩니다. '
             '<strong>self.run_action("ACTION_ID", value="959019d1-c1fa-41fe-a554-7be3366a9c5b")</strong>를 실행하면 지정된 ID의 PID 컨트롤러가 재개됩니다.',

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'PID'
            ],
            'name': lazy_gettext('컨트롤러'),
            'phrase': '재개할 PID 컨트롤러를 선택하세요'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: PID Resume."""
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
            controller_id = dict_vars["value"]["pid_id"]
        except:
            controller_id = self.controller_id

        pid = db_retrieve_table_daemon(
            PID, unique_id=controller_id, entry='first')

        if not pid:
            msg = f"오류: ID '{controller_id}'에 해당하는 PID 컨트롤러를 찾을 수 없습니다."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        dict_vars['message'] += f"PID {controller_id} ({pid.name})를 재개합니다."

        if not pid.is_paused:
            dict_vars['message'] += " 알림: PID가 일시 정지 상태가 아닙니다!"
        elif pid.is_activated:
            with session_scope(LOOPERGET_DB_PATH) as new_session:
                mod_pid = new_session.query(PID).filter(
                    PID.unique_id == controller_id).first()
                mod_pid.is_paused = False
                new_session.commit()
            resume_pid = threading.Thread(
                target=self.control.pid_resume,
                args=(controller_id,))
            resume_pid.start()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup