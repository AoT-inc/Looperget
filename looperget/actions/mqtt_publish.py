# coding=utf-8
from flask_babel import lazy_gettext

from looperget.databases.models import Actions
from looperget.actions.base_action import AbstractFunctionAction
from looperget.utils.constraints_pass import constraints_pass_positive_or_zero_value
from looperget.utils.database import db_retrieve_table_daemon
from looperget.utils.utils import random_alphanumeric

ACTION_INFORMATION = {
    'name_unique': 'mqtt_publish',
    'name': "MQTT: {}".format(lazy_gettext('발행')),
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'MQTT 서버에 값을 발행합니다.',

    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 저장된 페이로드 텍스트 옵션이 MQTT 서버에 발행됩니다. '
             '<strong>self.run_action("ACTION_ID", value={"payload": 42})</strong>를 실행하면 지정된 페이로드(모든 타입)가 MQTT 서버에 발행됩니다. '
             '또한 토픽을 지정할 수도 있습니다 (예: value={"topic": "my_topic", "payload": 42}). '
             '경고: 여러 MQTT 입력 또는 함수를 사용하는 경우, 클라이언트 ID가 고유한지 확인하십시오.',

    'dependencies_module': [
        ('pip-pypi', 'paho', 'paho-mqtt==1.5.1')
    ],

    'custom_options': [
        {
            'id': 'hostname',
            'type': 'text',
            'default_value': 'localhost',
            'required': True,
            'name': lazy_gettext('호스트명'),
            'phrase': 'MQTT 서버의 호스트명을 입력하세요'
        },
        {
            'id': 'port',
            'type': 'integer',
            'default_value': 1883,
            'required': True,
            'name': lazy_gettext('포트'),
            'phrase': 'MQTT 서버의 포트를 입력하세요'
        },
        {
            'id': 'topic',
            'type': 'text',
            'default_value': 'paho/test/single',
            'required': True,
            'name': '토픽',
            'phrase': '발행에 사용할 토픽을 입력하세요'
        },
        {
            'id': 'payload',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': '페이로드',
            'phrase': '발행할 페이로드를 입력하세요'
        },
        {
            'id': 'payload_type',
            'type': 'select',
            'default_value': 'text',
            'required': True,
            'options_select': [
                ('text', '텍스트'),
                ('integer', '정수'),
                ('float', '실수/소수')
            ],
            'name': '페이로드 유형',
            'phrase': '페이로드를 형 변환할 유형을 지정하세요'
        },
        {
            'id': 'keepalive',
            'type': 'integer',
            'default_value': 60,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': lazy_gettext('유지 시간'),
            'phrase': '클라이언트의 keepalive 타임아웃 값입니다. 0으로 설정하면 비활성화됩니다.'
        },
        {
            'id': 'clientid',
            'type': 'text',
            'default_value': f'client_{random_alphanumeric(8)}',
            'required': True,
            'name': '클라이언트 ID',
            'phrase': 'MQTT 서버에 연결하기 위한 고유 클라이언트 ID를 입력하세요'
        },
        {
            'id': 'login',
            'type': 'bool',
            'default_value': False,
            'name': '로그인 사용',
            'phrase': '로그인 자격 증명을 전송합니다.'
        },
        {
            'id': 'username',
            'type': 'text',
            'default_value': 'user',
            'required': False,
            'name': lazy_gettext('사용자 이름'),
            'phrase': '서버에 연결하기 위한 사용자 이름을 입력하세요'
        },
        {
            'id': 'password',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': lazy_gettext('비밀번호'),
            'phrase': '서버에 연결하기 위한 비밀번호를 입력하세요'
        },
        {
            'id': 'mqtt_use_websockets',
            'type': 'bool',
            'default_value': False,
            'required': False,
            'name': '웹소켓 사용',
            'phrase': '서버에 연결하기 위해 웹소켓을 사용합니다.'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """함수 동작: MQTT 발행."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.publish = None

        self.hostname = None
        self.port = None
        self.topic = None
        self.payload = None
        self.payload_type = None
        self.keepalive = None
        self.clientid = None
        self.login = None
        self.username = None
        self.password = None
        self.mqtt_use_websockets = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        import paho.mqtt.publish as publish
        self.publish = publish
        self.action_setup = True

    def run_action(self, dict_vars):
        try:
            topic = dict_vars["value"]["topic"]
        except:
            topic = self.topic

        try:
            payload = dict_vars["value"]["payload"]
        except:
            payload = self.payload

            try:
                if self.payload_type == 'integer':
                    payload = int(payload)
                elif self.payload_type == 'float':
                    payload = float(payload)
            except:
                msg = f"오류: 페이로드를 {self.payload_type}로 형 변환할 수 없습니다."
                self.logger.error(msg)
                dict_vars['message'] += msg
                return dict_vars

        if not payload:
            msg = "오류: 페이로드 없이 MQTT 서버에 발행할 수 없습니다."
            self.logger.error(msg)
            dict_vars['message'] += msg
            return dict_vars

        try:
            auth_dict = None
            if self.login:
                auth_dict = {
                    "username": self.username,
                    "password": self.password
                }
            self.publish.single(
                topic,
                payload,
                hostname=self.hostname,
                port=self.port,
                client_id=self.clientid,
                keepalive=self.keepalive,
                auth=auth_dict,
                transport='websockets' if self.mqtt_use_websockets else 'tcp')
            dict_vars['message'] += f" MQTT 발행 '{payload}'."
        except Exception as err:
            msg = f"MQTT 발행을 실행할 수 없습니다: {err}"
            self.logger.error(msg)
            dict_vars['message'] += msg

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup