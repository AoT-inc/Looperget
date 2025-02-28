# coding=utf-8
import http.client
import logging
import urllib
from urllib.parse import urlparse

from flask_gettext import lazy_gettext

from looperget.databases.models import Actions
from looperget.actions.base_action import AbstractFunctionAction
from looperget.utils.database import db_retrieve_table_daemon

ACTION_INFORMATION = {
    'name_unique': 'webhook',
    'name': lazy_gettext('웹훅'),
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': '트리거되면 HTTP 요청을 발생시킵니다. 첫 번째 줄에는 HTTP 메서드(GET, POST, PUT 등)와 호출할 URL이 공백으로 구분되어 포함됩니다. 이후 줄들은 선택적인 "이름: 값" 형태의 헤더 파라미터입니다. 빈 줄 이후에는 전송할 본문 페이로드가 이어집니다. {{{message}}}는 메시지로 대체되는 자리 표시자이며, {{{quoted_message}}}는 URL 안전 인코딩된 메시지입니다.',
    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 액션이 실행됩니다.',

    'custom_options': [
        {
            'id': 'webhook',
            'type': 'multiline_text',
            'lines': 7,
            'default_value': "",
            'required': True,
            'col_width': 12,
            'name': '웹훅 요청',
            'phrase': '실행할 HTTP 요청을 입력하세요'
        },
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: Webhook"""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.webhook = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.action_setup = True

    def run_action(self, dict_vars):
        action_string = self.webhook
        action_string = action_string.replace("{{{message}}}", dict_vars['message'])
        action_string = action_string.replace("{{{quoted_message}}}", urllib.parse.quote_plus(dict_vars['message']))
        lines = action_string.splitlines()

        method = "GET"

        # 첫 번째 줄은 "[<메서드> ]<URL>" 형식입니다. 이후 줄들은 HTTP 요청 헤더입니다.
        parts = lines.pop(0).split(" ", 1)
        if len(parts) == 1:
            url = parts[0]
        else:
            method = parts[0]
            url = parts[1]

        headers = []
        while len(lines) > 0:
            line = lines.pop(0)
            if line.strip() == "":
                break
            headers.append(map(str.strip, line.split(':', 1)))

        headers = dict(headers)
        parsed_url = urlparse(url)
        body = "\n".join(lines)

        path_and_query = parsed_url.path + "?" + parsed_url.query

        dict_vars['message'] += f" 웹훅 호출: 메서드: {method}, 스킴: {parsed_url.scheme}, 네트워크 위치: {parsed_url.netloc}, 경로: {path_and_query}, 헤더: {headers}, 본문: {body}."

        if parsed_url.scheme == 'http':
            conn = http.client.HTTPConnection(parsed_url.netloc)
        elif parsed_url.scheme == 'https':
            conn = http.client.HTTPSConnection(parsed_url.netloc)
        else:
            raise Exception(f"지원되지 않는 URL 스킴 '{parsed_url.scheme}'입니다.")

        conn.request(method, path_and_query, body, headers)
        response = conn.getresponse()
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(response.readlines())
        if 200 <= response.getcode() < 300:
            self.logger.debug(f"HTTP {response.getcode()} -> 정상")
        else:
            raise Exception(f"HTTP {response.getcode()} 응답을 받았습니다.")
        response.close()

        self.logger.debug(f"메시지: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup