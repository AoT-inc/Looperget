# coding=utf-8
from flask_babel import lazy_gettext

from looperget.actions.base_action import AbstractFunctionAction
from looperget.databases.models import Actions
from looperget.utils.constraints_pass import constraints_pass_positive_or_zero_value
from looperget.utils.database import db_retrieve_table_daemon
from looperget.utils.system_pi import get_measurement
from looperget.utils.utils import random_alphanumeric

ACTION_INFORMATION = {
    'name_unique': 'mqtt_publish_input',
    'name': "MQTT: {}: {}".format(lazy_gettext('발행'), lazy_gettext('측정')),
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['inputs'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': "MQTT 서버에 입력 측정을 발행합니다.",

    'usage': '',

    'dependencies_module': [
        ('pip-pypi', 'paho', 'paho-mqtt==1.5.1')
    ],

    'custom_options': [
        {
            'id': 'measurement',
            'type': 'select_measurement_from_this_input',
            'default_value': None,
            'name': lazy_gettext('측정'),
            'phrase': '페이로드로 전송할 측정을 선택하세요'
        },
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
            'phrase': '서버에 연결하기 위한 비밀번호를 입력하세요.'
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
    """Function Action: MQTT Publish."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.publish = None

        self.measurement_device_id = None
        self.measurement_measurement_id = None

        self.hostname = None
        self.port = None
        self.topic = None
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
        device_measurement = get_measurement(
            self.measurement_measurement_id)

        if not device_measurement:
            msg = "오류: 페이로드로 사용할 측정값을 선택해야 합니다."
            self.logger.error(msg)
            dict_vars["message"] += msg
            return dict_vars

        channel = device_measurement.channel

        try:
            payload = dict_vars["measurements_dict"][channel]['value']
        except:
            payload = None

        self.logger.debug(f"Input channel: {channel}, payload: {payload}")

        if payload is None:
            msg = f"오류: {channel}에 대한 페이로드에서 측정값을 찾을 수 없습니다."
            self.logger.error(msg)
            dict_vars["message"] += msg
            return dict_vars

        try:
            auth_dict = None
            if self.login:
                auth_dict = {
                    "username": self.username,
                    "password": self.password
                }
            self.publish.single(
                self.topic,
                payload,
                hostname=self.hostname,
                port=self.port,
                client_id=self.clientid,
                keepalive=self.keepalive,
                auth=auth_dict,
                transport='websockets' if self.mqtt_use_websockets else 'tcp')
            dict_vars["message"] += f" MQTT 발행 '{payload}'."
        except Exception as err:
            msg = f"MQTT 발행을 실행할 수 없습니다: {err}"
            self.logger.error(msg)
            dict_vars["message"] += msg

        return dict_vars

    def is_setup(self):
        return self.action_setup