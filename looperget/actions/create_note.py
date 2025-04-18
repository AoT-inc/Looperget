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
    'message': lazy_gettext('Create a note with the selected Tag.'),
    'library': None,
    'manufacturer': 'Looperget',
    'application': ['functions'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'usage': 'Executing <strong>self.run_action("ACTION_ID")</strong> will create a note with the selected tag and note. '
             'Executing <strong>self.run_action("ACTION_ID", value={"tags": ["tag1", "tag2"], "name": "My Note", "note": "this is a message"})</strong> will execute the action with the specified list of tag(s) and note. If using only one tag, make it the only element of the list (e.g. ["tag1"]). If note is not specified, then the action message will be used as the note.',

    'custom_options': [
        {
            'id': 'tag',
            'type': 'select_multi_measurement',
            'default_value': '',
            'options_select': [
                'Tag'
            ],
            'name': lazy_gettext('Tags'),
            'phrase': 'Select one or more tags'
        },
        {
            'id': 'name',
            'type': 'text',
            'default_value': 'Name',
            'required': False,
            'name': lazy_gettext('Name'),
            'phrase': 'The name of the note'
        },
        {
            'id': 'note',
            'type': 'text',
            'default_value': 'Note',
            'required': False,
            'name': lazy_gettext('Note'),
            'phrase': 'The body of the note'
        },
        {
            'id': 'include_message',
            'type': 'bool',
            'default_value': False,
            'name': 'Include Message in Note',
            'phrase': "Include the message passed to the action in the note that's created"
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
                msg = "No valid tags specified. Cannot create note."
                dict_vars['message'] += msg
                self.logger.error(msg)
                return dict_vars

            dict_vars['message'] += f" Create note with name '{name}', tag ID(s) '{','.join(list_tag_ids)}'"
            if note:
                dict_vars['message'] += f", and note {note}"
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
