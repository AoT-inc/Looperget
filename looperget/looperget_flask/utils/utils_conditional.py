# -*- coding: utf-8 -*-
import logging
import os

import sqlalchemy
from flask import current_app
from markupsafe import Markup

from looperget.config import PATH_PYTHON_CODE_USER
from looperget.config_translations import TRANSLATIONS
from looperget.databases.models import Actions
from looperget.databases.models import Conditional
from looperget.databases.models import ConditionalConditions
from looperget.looperget_client import DaemonControl
from looperget.looperget_flask.extensions import db
from looperget.looperget_flask.utils.utils_general import controller_activate_deactivate
from looperget.looperget_flask.utils.utils_general import delete_entry_with_id
from looperget.utils.conditional import save_conditional_code

logger = logging.getLogger(__name__)


def conditional_mod(form):
    """조건부 기능 수정."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": [],
        "page_refresh": True,
        "return_text": [],
        "name": None
    }

    cmd_status = None
    pylint_message = ""

    try:
        if not current_app.config['TESTING']:
            messages["error"], lines_code, cmd_status, cmd_out = save_conditional_code(
                messages["error"],
                form.conditional_import.data,
                form.conditional_initialize.data,
                form.conditional_statement.data,
                form.conditional_status.data,
                form.function_id.data,
                ConditionalConditions.query.all(),
                Actions.query.all(),
                timeout=form.pyro_timeout.data,
                test=form.use_pylint.data)

            code_str = f"<pre>\n\n전체 조건부 코드:\n\n{lines_code}"
            if form.use_pylint.data:
                code_str += f'\npylint 코드 분석:\n\n{cmd_out.decode("utf-8")}'
            code_str += "</pre>"
            pylint_message = Markup(code_str)

        cond_mod = Conditional.query.filter(
            Conditional.unique_id == form.function_id.data).first()
        cond_mod.name = form.name.data
        messages["name"] = form.name.data
        cond_mod.conditional_import = form.conditional_import.data
        cond_mod.conditional_initialize = form.conditional_initialize.data
        cond_mod.conditional_statement = form.conditional_statement.data
        cond_mod.conditional_status = form.conditional_status.data
        cond_mod.period = form.period.data
        cond_mod.log_level_debug = form.log_level_debug.data
        cond_mod.use_pylint = form.use_pylint.data
        cond_mod.message_include_code = form.message_include_code.data
        cond_mod.start_offset = form.start_offset.data
        cond_mod.pyro_timeout = form.pyro_timeout.data

        if cmd_status:
            messages["warning"].append(
                "pylint가 상태 {}를 반환했습니다. 경고는 오류가 아님을 참고하세요. 이는 pylint 분석이 완벽한 10점을 반환하지 않았음을 나타냅니다.".format(cmd_status))

        if pylint_message:
            messages["info"].append("코드에 문제가 없는지 검토하고, 프로덕션 환경에 적용하기 전에 테스트하세요.")
            messages["return_text"].append(pylint_message)

        if not messages["error"]:
            db.session.commit()
            messages["success"].append("조건부 기능 수정 완료")

            if cond_mod.is_activated:
                control = DaemonControl()
                return_value = control.refresh_daemon_conditional_settings(form.function_id.data)
                messages["success"].append("데몬 응답: {}".format(return_value))

    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages


def conditional_del(cond_id):
    """조건부 기능 삭제."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    cond = Conditional.query.filter(Conditional.unique_id == cond_id).first()

    # 활성화되어 있는 경우 조건부 기능 비활성화
    if cond.is_activated:
        conditional_deactivate(cond_id)

    try:
        if not messages["error"]:
            # 조건 삭제
            conditions = ConditionalConditions.query.filter(
                ConditionalConditions.conditional_id == cond_id).all()
            for each_condition in conditions:
                delete_entry_with_id(ConditionalConditions, each_condition.unique_id, flash_message=False)

            # 액션 삭제
            actions = Actions.query.filter(Actions.function_id == cond_id).all()
            for each_action in actions:
                delete_entry_with_id(Actions, each_action.unique_id, flash_message=False)

            delete_entry_with_id(Conditional, cond_id, flash_message=False)

            messages["success"].append("조건부 기능 삭제 완료")

            try:
                file_path = os.path.join(PATH_PYTHON_CODE_USER, 'conditional_{}.py'.format(cond.unique_id))
                os.remove(file_path)
            except:
                pass

            db.session.commit()
    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages


def conditional_condition_add(form):
    """조건부 조건 추가."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }
    condition_id = None

    cond = Conditional.query.filter(Conditional.unique_id == form.function_id.data).first()
    if cond.is_activated:
        messages["error"].append("조건을 추가하기 전에 조건부 기능을 비활성화하세요.")

    if form.condition_type.data == '':
        messages["error"].append("조건을 선택해야 합니다.")

    try:
        new_condition = ConditionalConditions()
        new_condition.conditional_id = form.function_id.data
        new_condition.condition_type = form.condition_type.data

        if new_condition.condition_type == 'measurement':
            new_condition.max_age = 360

        if not messages["error"]:
            new_condition.save()
            condition_id = new_condition.unique_id
            messages["success"].append("조건부 조건 추가 완료")

    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages, condition_id


def conditional_condition_mod(form):
    """조건부 조건 수정."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    try:
        cond_mod = ConditionalConditions.query.filter(
            ConditionalConditions.unique_id == form.conditional_condition_id.data).first()

        conditional = Conditional.query.filter(
            Conditional.unique_id == cond_mod.conditional_id).first()

        if cond_mod.condition_type in ['measurement', 'measurement_and_ts', 'measurement_past_average', 'measurement_past_sum', 'measurement_dict']:
            messages["error"] = check_form_measurements(form, messages["error"])
            cond_mod.measurement = form.measurement.data
            cond_mod.max_age = form.max_age.data

        elif cond_mod.condition_type == 'gpio_state':
            cond_mod.gpio_pin = form.gpio_pin.data

        elif cond_mod.condition_type in ['output_state', 'output_duration_on']:
            cond_mod.output_id = form.output_id.data

        elif cond_mod.condition_type == 'controller_status':
            cond_mod.controller_id = form.controller_id.data

        if not messages["error"]:
            db.session.commit()
            messages["success"].append("조건부 조건 수정 완료")

            if conditional.is_activated:
                control = DaemonControl()
                return_value = control.refresh_daemon_conditional_settings(form.conditional_id.data)
                messages["success"].append("데몬 응답: {}".format(return_value))

    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages


def conditional_condition_del(form):
    """조건부 조건 삭제."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    condition = ConditionalConditions.query.filter(
        ConditionalConditions.unique_id == form.conditional_condition_id.data).first()
    if not condition:
        messages["error"].append("조건을 찾을 수 없습니다.")

    conditional = Conditional.query.filter(
        Conditional.unique_id == condition.conditional_id).first()
    if conditional.is_activated:
        messages["error"].append("조건을 삭제하기 전에 조건부 기능을 비활성화하세요.")

    try:
        if not messages["error"]:
            delete_entry_with_id(ConditionalConditions, condition.unique_id, flash_message=False)
            messages["success"].append("조건부 조건 삭제 완료")

    except sqlalchemy.exc.OperationalError as except_msg:
        messages["error"].append(str(except_msg))
    except sqlalchemy.exc.IntegrityError as except_msg:
        messages["error"].append(str(except_msg))
    except Exception as except_msg:
        messages["error"].append(str(except_msg))

    return messages


def conditional_activate(cond_id):
    """조건부 기능 활성화."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    conditions = ConditionalConditions.query.filter(
        ConditionalConditions.conditional_id == cond_id).all()

    for each_condition in conditions:
        messages["success"] = check_cond_conditions(each_condition, messages["success"])

    conditions_query = ConditionalConditions.query.filter(ConditionalConditions.conditional_id == cond_id)
    if not conditions_query.count():
        messages["info"].append("조건 없이 조건부 기능이 활성화되었습니다. 일반적으로 조건부 기능은 조건을 사용합니다. 조건 없이 진행하려면 충분히 이해한 경우에만 진행하세요.")

    actions = Actions.query.filter(Actions.function_id == cond_id)
    if not actions.count():
        messages["info"].append("동작 없이 조건부 기능이 활성화되었습니다. 일반적으로 조건부 기능은 동작을 사용합니다. 동작 없이 진행하려면 충분히 이해한 경우에만 진행하세요.")

    messages = controller_activate_deactivate(messages, 'activate', 'Conditional', cond_id, flash_message=False)

    if not messages["success"]:
        messages["success"].append("조건부 기능 활성화 완료")

    return messages


def conditional_deactivate(cond_id):
    """조건부 기능 비활성화."""
    messages = {
        "success": [],
        "info": [],
        "warning": [],
        "error": []
    }

    messages = controller_activate_deactivate(messages, 'deactivate', 'Conditional', cond_id, flash_message=False)

    if not messages["error"]:
        messages["success"].append("조건부 기능 비활성화 완료")

    return messages


def check_form_measurements(form, error):
    """제출된 폼에 오류가 있는지 확인합니다."""
    if not form.measurement.data or form.measurement.data == '':
        error.append("{meas}를 설정해야 합니다.".format(meas=form.measurement.label.text))
    if not form.max_age.data or form.max_age.data <= 0:
        error.append("{dir}는 0보다 커야 합니다.".format(dir=form.max_age.label.text))
    return error


def check_cond_conditions(cond, error):
    """저장된 변수에 오류가 있는지 확인합니다."""
    if (cond.condition_type == 'measurement' and (not cond.measurement or cond.measurement == '')):
        error.append("측정값이 설정되어야 합니다. ID가 {id}로 시작하는 조건이 설정되지 않았습니다.".format(id=cond.unique_id.split('-')[0]))
    if (cond.condition_type == 'output_state' and (not cond.output_id or cond.output_id == '')):
        error.append("출력이 설정되어야 합니다. ID가 {id}로 시작하는 조건이 설정되지 않았습니다.".format(id=cond.unique_id.split('-')[0]))
    if cond.condition_type == 'gpio_state' and not cond.gpio_pin:
        error.append("GPIO 핀이 설정되어야 합니다. ID가 {id}로 시작하는 조건이 설정되지 않았습니다.".format(id=cond.unique_id.split('-')[0]))
    if not cond.max_age or cond.max_age <= 0:
        error.append("최대 나이는 0보다 커야 합니다.")
    return error