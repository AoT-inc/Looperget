# coding=utf-8
from flask_babel import lazy_gettext

from looperget.config_translations import TRANSLATIONS
from looperget.databases.models import Actions
from looperget.databases.models import Camera
from looperget.devices.camera import camera_record
from looperget.actions.base_action import AbstractFunctionAction
from looperget.utils.database import db_retrieve_table_daemon


ACTION_INFORMATION = {
    'name_unique': 'photo',
    'name': "{}: {}".format(TRANSLATIONS['camera']['title'], lazy_gettext('사진 촬영')),
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': lazy_gettext('선택한 카메라로 사진을 촬영합니다.'),

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong>를 실행하면 선택한 카메라로 사진을 촬영합니다. '
             'Executing <strong>self.run_action("ACTION_ID", value={"camera_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b"})</strong>를 실행하면 지정된 ID의 카메라로 사진을 촬영합니다. '
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
            'phrase': '사진 촬영에 사용할 카메라를 선택하세요'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Capture Photo."""
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

        camera = db_retrieve_table_daemon(
            Camera, unique_id=controller_id, entry='first')

        if not camera:
            msg = f"오류: ID '{controller_id}'에 해당하는 카메라를 찾을 수 없습니다."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        dict_vars['message'] += f"카메라 {controller_id} ({camera.name})로 사진을 촬영합니다."

        path, filename = camera_record('photo', controller_id)
        if not path and not filename:
            msg = " 이미지를 획득할 수 없습니다."
            self.logger.error(msg)
            dict_vars['message'] += msg

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup