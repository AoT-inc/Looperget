# coding=utf-8
from flask_babel import lazy_gettext

from looperget.actions.base_action import AbstractFunctionAction
from looperget.config import LOOPERGET_DB_PATH
from looperget.config_translations import TRANSLATIONS
from looperget.databases.models import Actions
from looperget.databases.models import Camera
from looperget.databases.utils import session_scope
from looperget.utils.database import db_retrieve_table_daemon


ACTION_INFORMATION = {
    'name_unique': 'camera_timelapse_resume',
    'name': f"{TRANSLATIONS['camera']['title']}: {TRANSLATIONS['timelapse']['title']}: {TRANSLATIONS['resume']['title']}",
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': '카메라 타임랩스를 재개합니다.',

    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 선택한 카메라 타임랩스가 재개됩니다. '
             '<strong>self.run_action("ACTION_ID", value={"camera_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong>를 실행하면 지정된 ID의 카메라 타임랩스가 재개됩니다. '
             '시스템에 존재하는 실제 카메라 ID로 camera_id 값을 변경하는 것을 잊지 마십시오.',

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Camera'
            ],
            'name': lazy_gettext('카메라'),
            'phrase': '타임랩스를 재개할 카메라를 선택하세요'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Camera Time-lapse Resume."""
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
            controller_id = dict_vars["value"]["camera_id"]
        except:
            controller_id = self.controller_id

        this_camera = db_retrieve_table_daemon(
            Camera, unique_id=controller_id, entry='first')

        if not this_camera:
            msg = f"오류: ID '{controller_id}'에 해당하는 카메라를 찾을 수 없습니다."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        dict_vars['message'] += f"카메라 {controller_id} ({this_camera.name})의 타임랩스를 재개합니다."
        with session_scope(LOOPERGET_DB_PATH) as new_session:
            mod_camera = new_session.query(Camera).filter(
                Camera.unique_id == controller_id).first()
            mod_camera.timelapse_paused = False
            new_session.commit()

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup