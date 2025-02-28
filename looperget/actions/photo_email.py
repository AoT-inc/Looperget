# coding=utf-8
import os
import time

from flask_babel import lazy_gettext

from looperget.databases.models import Actions
from looperget.databases.models import Camera
from looperget.databases.models import SMTP
from looperget.devices.camera import camera_record
from looperget.actions.base_action import AbstractFunctionAction
from looperget.utils.database import db_retrieve_table_daemon
from looperget.utils.actions import check_allowed_to_email
from looperget.utils.send_data import send_email

ACTION_INFORMATION = {
    'name_unique': 'photo_email',
    'name': '사진 첨부 이메일 전송',
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': '사진을 촬영하고 첨부된 이메일을 전송합니다.',
    
    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 시스템 구성에 설정된 SMTP 자격증명을 사용하여 사진을 촬영하고 지정된 수신자에게 이메일을 전송합니다. '
             '여러 수신자는 콤마(,)로 구분합니다. 이메일 본문은 자동 생성된 메시지가 사용됩니다. '
             '<strong>self.run_action("ACTION_ID", value={"camera_id": "959019d1-c1fa-41fe-a554-7be3366a9c5b", "email_address": ["email1@email.com", "email2@email.com"], "message": "My message"})</strong>를 실행하면, '
             '지정된 ID의 카메라로 사진을 촬영하고 해당 사진을 첨부하여 지정된 이메일 주소로 메시지를 전송합니다. '
             '실제 시스템에 존재하는 카메라 ID로 camera_id 값을 변경하는 것을 잊지 마십시오.',
    
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
        },
        {
            'id': 'email',
            'type': 'text',
            'default_value': 'email@domain.com',
            'required': True,
            'name': '이메일 주소',
            'phrase': '수신자 이메일 주소를 입력하세요. 여러 주소는 콤마(,)로 구분합니다.'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """함수 동작: 사진 첨부 이메일 전송."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.controller_id = None
        self.email = None

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

        try:
            email_recipients = dict_vars["value"]["email_address"]
        except:
            if "," in self.email:
                email_recipients = self.email.split(",")
            else:
                email_recipients = [self.email]

        if not email_recipients:
            msg = "오류: 수신자가 지정되지 않았습니다."
            self.logger.error(msg)
            dict_vars['message'] += msg
            return dict_vars

        try:
            message_send = dict_vars["value"]["message"]
        except:
            message_send = None

        this_camera = db_retrieve_table_daemon(
            Camera, unique_id=controller_id, entry='first')

        if not this_camera:
            msg = f"오류: ID '{controller_id}'에 해당하는 카메라를 찾을 수 없습니다."
            dict_vars['message'] += msg
            self.logger.error(msg)
            return dict_vars

        path, filename = camera_record('photo', this_camera.unique_id)
        if path and filename:
            attachment_file = os.path.join(path, filename)
            smtp_wait_timer, allowed_to_send_notice = check_allowed_to_email()
            if allowed_to_send_notice:
                dict_vars['message'] += f" 이메일 '{','.join(email_recipients)}'로 사진 첨부 이메일을 전송합니다."
                if not message_send:
                    message_send = dict_vars['message']
                smtp = db_retrieve_table_daemon(SMTP, entry='first')
                send_email(smtp.host, smtp.protocol, smtp.port,
                           smtp.user, smtp.passw, smtp.email_from,
                           email_recipients, message_send,
                           attachment_file=attachment_file,
                           attachment_type="still")
            else:
                self.logger.error(
                    f"이메일 전송을 다시 시도하기 전에 {smtp_wait_timer - time.time():.0f}초 기다리세요.")
        else:
            dict_vars['message'] += " 이미지를 획득할 수 없으므로 이메일을 전송하지 않습니다."

        self.logger.debug(f"메시지: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup