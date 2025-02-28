# coding=utf-8
from flask_babel import lazy_gettext

from looperget.actions.base_action import AbstractFunctionAction
from looperget.config import LOOPERGET_DB_PATH
from looperget.config_translations import TRANSLATIONS
from looperget.databases.models import Actions
from looperget.databases.models import NoteTags
from looperget.databases.models import Notes
from looperget.databases.utils import session_scope
from looperget.utils.database import db_retrieve_table_daemon


ACTION_INFORMATION = {
    'name_unique': 'create_note',
    'name': f"{TRANSLATIONS['create']['title']}: {TRANSLATIONS['note']['title']}",
    'message': lazy_gettext('선택된 태그로 노트를 생성합니다.'),
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'usage': '<strong>self.run_action("ACTION_ID")</strong>를 실행하면 선택한 태그와 노트로 노트가 생성됩니다. '
             '<strong>self.run_action("ACTION_ID", value={"tags": ["tag1", "tag2"], "name": "My Note", "note": "this is a message"})</strong>를 실행하면 지정된 태그 목록과 노트를 사용하여 작업이 실행됩니다. '
             '태그가 하나만 사용되는 경우, 리스트의 유일한 요소로 만드십시오 (예: ["tag1"]). '
             '노트가 지정되지 않은 경우, 작업 메시지가 노트로 사용됩니다.',

    'custom_options': [
        {
            'id': 'tag',
            'type': 'select_multi_measurement',
            'default_value': '',
            'options_select': [
                'Tag'
            ],
            'name': lazy_gettext('태그'),
            'phrase': '하나 이상의 태그를 선택하세요'
        },
        {
            'id': 'name',
            'type': 'text',
            'default_value': 'Name',
            'required': False,
            'name': lazy_gettext('이름'),
            'phrase': '노트의 이름'
        },
        {
            'id': 'note',
            'type': 'text',
            'default_value': 'Note',
            'required': False,
            'name': lazy_gettext('노트'),
            'phrase': '노트의 본문'
        },
        {
            'id': 'include_message',
            'type': 'bool',
            'default_value': False,
            'name': '생성된 노트에 메시지 포함',
            'phrase': "생성된 노트에 작업으로 전달된 메시지를 포함합니다."
        }
    ]
}

class ActionModule(AbstractFunctionAction):
    """Function Action: Create Note."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.tag = None
        self.name = None
        self.note = None
        self.include_message = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.action_setup = True

    def run_action(self, dict_vars):
        list_tags = []
        try:
            list_tags = dict_vars["value"]["tags"]
        except:
            for each_id_set in self.tag:
                list_tags.append(each_id_set.split(",")[0])

        try:
            name = dict_vars["value"]["name"]
        except:
            name = self.name

        try:
            note = dict_vars["value"]["note"]
        except:
            note = self.note

        if self.include_message and 'message' in dict_vars:
            note += f"\n\n{dict_vars['message']}"

        self.logger.debug(f"Tag(s): {','.join(list_tags)}, name: {name}, note: '{note}'.")

        with session_scope(LOOPERGET_DB_PATH) as new_session:
            list_tag_ids = []
            for each_tag in list_tags:
                tag_check = new_session.query(NoteTags).filter(
                    NoteTags.unique_id == each_tag).first()
                if tag_check:
                    list_tag_ids.append(each_tag)
                else:
                    self.logger.error(f"Tag with ID '{each_tag}' does not exist.")

            if not list_tag_ids:
                msg = "유효한 태그가 지정되지 않았습니다. 노트를 생성할 수 없습니다."
                dict_vars['message'] += msg
                self.logger.error(msg)
                return dict_vars

            dict_vars['message'] += f" 이름 '{name}', 태그 ID(s) '{','.join(list_tag_ids)}'로 노트를 생성합니다"
            if note:
                dict_vars['message'] += f", 노트는 {note}"
            dict_vars['message'] += "."

            new_note = Notes()
            new_note.name = name
            new_note.tags = ','.join(list_tag_ids)
            if note:
                new_note.note = note
            new_session.add(new_note)

        self.logger.debug(f"Message: {dict_vars['message']}")

        return dict_vars

    def is_setup(self):
        return self.action_setup