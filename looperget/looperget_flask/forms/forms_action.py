# -*- coding: utf-8 -*-
#
# forms_action.py - Function Flask Forms
#
import logging

from flask_wtf import FlaskForm
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import widgets

from looperget.config_translations import TRANSLATIONS

logger = logging.getLogger("looperget.forms_action")


class Actions(FlaskForm):
    action_type = SelectField("Action Type")
    device_id = StringField(
        'Device ID', widget=widgets.HiddenInput())
    function_type = StringField(
        'function_type', widget=widgets.HiddenInput())
    action_id = StringField(
        'Action ID', widget=widgets.HiddenInput())

    add_action = SubmitField(TRANSLATIONS['add']['title'])
    save_action = SubmitField(TRANSLATIONS['저장']['title'])
    delete_action = SubmitField(TRANSLATIONS['삭제']['title'])
