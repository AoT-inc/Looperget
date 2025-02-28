# coding=utf-8
import time

from looperget.databases.models import Actions
from looperget.databases.models import SMTP
from looperget.actions.base_action import AbstractFunctionAction
from looperget.utils.database import db_retrieve_table_daemon
from looperget.utils.actions import check_allowed_to_email
from looperget.utils.send_data import send_email

ACTION_INFORMATION = {
    'name_unique': 'email',
    'name': '이메일 보내기',
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': '이메일을 전송합니다.',

    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 시스템 구성에 설정된 SMTP 자격증명을 사용하여 지정된 수신자에게 이메일을 전송합니다. 여러 수신자는 콤마로 구분합니다. 이메일 본문은 자동 생성된 메시지가 됩니다. '
             '<strong>self.run_action("ACTION_ID", value={"email_address": ["email1@email.com", "email2@email.com"], "message": "My message"})</strong>를 실행하면 지정된 수신자에게 지정된 메시지로 이메일을 전송합니다.',

    'custom_options': [
        {
            'id': 'email',
            'type': 'text',
            'default_value': 'email@domain.com',
            'required': True,
            'name': '이메일',
            'phrase': '수신자 이메일 (여러 주소는 콤마로 구분)'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Send Email."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

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
            email_recipients = dict_vars["value"]["email_address"]
        except:
            if "," in self.email:
                email_recipients = self.email.split(",")
            else:
                email_recipients = [self.email]

        if not email_recipients:
            msg = f" 오류: 수신자가 지정되지 않았습니다."
            self.logger.error(msg)
            dict_vars['message'] += msg
            return dict_vars

        try:
            message_send = dict_vars["value"]["message"]
        except:
            message_send = False

        # If the emails per hour limit has not been exceeded
        smtp_wait_timer, allowed_to_send_notice = check_allowed_to_email()
        if allowed_to_send_notice:
            dict_vars['message'] += f" 이메일 '{self.email}'."
            if not message_send:
                message_send = dict_vars['message']
            smtp = db_retrieve_table_daemon(SMTP, entry='first')
            send_email(smtp.host, smtp.protocol, smtp.port,
                       smtp.user, smtp.passw, smtp.email_from,
                       email_recipients, message_send)
        else:
            self.logger.error(
                f"Wait {smtp_wait_timer - time.time():.0f} seconds to email again.")

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup