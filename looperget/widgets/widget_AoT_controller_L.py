# -*- coding: utf-8 -*-
"""
[새로운 AoT 위젯] widget_AoT_controller_act_deact.py

- 성공/실패 메시지 Toastr 제거 (유지)
- refresh_seconds 주기로 서버 상태를 업데이트하도록 setInterval 복원
- 나머지 기능(버튼 이벤트, UI 로직 등)은 그대로 유지
"""

import logging
from flask import jsonify
from flask_babel import lazy_gettext
from flask_login import current_user

from looperget.databases.models import Conditional, CustomController, Function, Input, Trigger
from looperget.looperget_client import DaemonControl
from looperget.looperget_flask.utils.utils_general import user_has_permission
from looperget.utils.constraints_pass import constraints_pass_positive_value

logger = logging.getLogger(__name__)

def controller_state(unique_id):
    if not current_user.is_authenticated:
        return "You are not logged in and cannot access this endpoint"

    input_ = Input.query.filter(Input.unique_id == unique_id).first()
    function = Function.query.filter(Function.unique_id == unique_id).first()
    customfunction = CustomController.query.filter(CustomController.unique_id == unique_id).first()
    trigger = Trigger.query.filter(Trigger.unique_id == unique_id).first()
    conditional = Conditional.query.filter(Conditional.unique_id == unique_id).first()

    controller = None
    if input_:
        controller = input_
    elif function:
        controller = function
    elif customfunction:
        controller = customfunction
    elif trigger:
        controller = trigger
    elif conditional:
        controller = conditional

    if controller:
        return jsonify({"status": "Success", "state": controller.is_activated})

    return jsonify({"status": "Error", "state": f"Could not find Controller with ID {unique_id}"})


def controller_activate_deactivate(unique_id, state):
    """Activate/Deactivate Controller (Input/Function/Trigger/Conditional/CustomController)."""
    if not current_user.is_authenticated:
        return "You are not logged in and cannot access this endpoint"
    if not user_has_permission('edit_controllers'):
        return 'Insufficient user permissions to manipulate Controller'

    input_ = Input.query.filter(Input.unique_id == unique_id).first()
    function = Function.query.filter(Function.unique_id == unique_id).first()
    customfunction = CustomController.query.filter(CustomController.unique_id == unique_id).first()
    trigger = Trigger.query.filter(Trigger.unique_id == unique_id).first()
    conditional = Conditional.query.filter(Conditional.unique_id == unique_id).first()

    controller = None
    if input_:
        controller = input_
    elif function:
        controller = function
    elif customfunction:
        controller = customfunction
    elif trigger:
        controller = trigger
    elif conditional:
        controller = conditional

    if not controller or not unique_id or state not in ['activate', 'deactivate']:
        return "Invalid inputs: Controller ID or State"

    daemon = DaemonControl()
    if state == 'activate':
        controller.is_activated = True
        controller.save()
        _, return_str = daemon.controller_activate(unique_id)
        return return_str
    elif state == 'deactivate':
        controller.is_activated = False
        controller.save()
        _, return_str = daemon.controller_deactivate(unique_id)
        return return_str

WIDGET_INFORMATION = {
    'widget_name_unique': 'AoT_controller_act_deact',
    'widget_name': 'AoT 컨트롤러 스위치',
    'widget_library': '',
    'no_class': True,

    'message': '컨트롤러를 켜고 끌 수 있는 스위치.',

    'widget_width': 24,
    'widget_height': 5,

    'endpoints': [
        ("/controller_state/<unique_id>", "controller_state", controller_state, ["GET"]),
        ("/controller_activate_deactivate/<unique_id>/<state>", "controller_activate_deactivate", controller_activate_deactivate, ["GET"])
    ],

    'custom_options': [
        {
            'id': 'controller',
            'type': 'select_device',
            'default_value': '',
            'options_select': [
                'Input',
                'Function',
                'Conditional',
                'Trigger'
                # PID, CustomController 등은 필요시 확장 가능
            ],
            'name': lazy_gettext('컨트롤러'),
            'phrase': lazy_gettext('컨트롤러를 선택하세요.')
        },
        {
            'id': 'refresh_seconds',
            'type': 'float',
            'default_value': 3.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': '{} ({})'.format(lazy_gettext("새로고침"), lazy_gettext("초")),
            'phrase': '위젯을 주기적으로 새로 고침하는 간격 (초)'
        }
    ],

    # -------------------- HEAD (CSS) --------------------
    'widget_dashboard_head': """
    <style>
      .pause-background-aotctrl {
        background-color: #fff3cd!important; 
      }
      .active-background-aotctrl {
        background-color: #FFF9E3!important; 
      }
      .inactive-background-aotctrl {
        background-color: #E9E9E9!important; 
      }

      .toggle-switch-aotctrl {
        position: relative;
        display: inline-block;
        margin-top: 0.8em; 
        margin-right: 0.5em; 
        width: 3.2em;
        height: 2em;
        vertical-align: middle;
      }
      .toggle-switch-aotctrl input {
        opacity: 0; width: 0; height: 0;
      }
      .slider-aotctrl {
        position: absolute;
        cursor: pointer;
        top: 0; left: 0; right: 0; bottom: 0;
        border-radius: 2em;
        background-color: #929292;
        transition: 0.3s;
      }
      .slider-aotctrl:before {
        position: absolute;
        content: "";
        height: 1.6em;
        width: 1.6em;
        left: 0.2em;
        bottom: 0.2em;
        background-color: #fff;
        border-radius: 100%;
        transition: 0.3s;
      }
      .toggle-switch-aotctrl input:checked + .slider-aotctrl {
        background-color: #F4D624;
      }
      .toggle-switch-aotctrl input:checked + .slider-aotctrl:before {
        transform: translateX(1.2em);
      }

      .mobile-aotctrl-widget {
        display: flex;
        flex-direction: column;
        width: 100%;
        height: 100%;
        box-sizing: border-box;
        overflow: hidden;
        background-color: #E9E9E9; /* OFF=연분홍 */
        transition: background-color 0.3s;
      }

      .controller-header-row-aotctrl {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
    </style>
    """,

    # -------------------- TITLE BAR --------------------
    'widget_dashboard_title_bar': """
{%- if each_widget.name %}
  <span>{{ each_widget.name }}</span>
{%- else %}
  <span>컨트롤러 스위치</span>
{%- endif %}
""",

    # -------------------- BODY --------------------
    'widget_dashboard_body': """
<div id="container-aotctrl-{{each_widget.unique_id}}"
     class="mobile-aotctrl-widget inactive-background-aotctrl">

  <div style="width:100%; height:100%; box-sizing:border-box;">

    <!-- 1행: 상태 문구(왼쪽) + 토글(오른쪽) -->
    <div class="controller-header-row-aotctrl">
      <span id="text-controller-state-{{each_widget.unique_id}}"
            style="margin-left:0.5em;">
        (Inactive)
      </span>
      <label class="toggle-switch-aotctrl">
        <input type="checkbox"
               id="ctrl_toggle_{{each_widget.unique_id}}"
               class="controller_onoff_chk">
        <span class="slider-aotctrl"></span>
      </label>
    </div>
    
    <!-- 필요시 추가 UI 요소 배치 -->

  </div>
</div>
""",

    # -------------------- JAVASCRIPT --------------------
    'widget_dashboard_js': """
function printControllerErrorAoT(wid){
  let contDiv = document.getElementById("container-aotctrl-"+wid);
  if(contDiv){
    contDiv.classList.remove("pause-background-aotctrl",
                             "active-background-aotctrl",
                             "inactive-background-aotctrl");
    contDiv.classList.add("inactive-background-aotctrl");
  }
  let stateSpan = document.getElementById("text-controller-state-"+wid);
  if(stateSpan){
    stateSpan.innerHTML = "(Error)";
  }
}

// 컨트롤러 상태 확인 (1회)
function getControllerStateAoT(wid, dev_id){
  $.ajax({
    url: "/controller_state/"+dev_id,
    type: "GET",
    success: function(data, textStatus, jqXHR){
      if(data.status === "Error"){
        printControllerErrorAoT(wid);
      } else {
        // data.state => true/false
        let isActive = data.state;
        updateControllerUIAoT(wid, isActive);
      }
    },
    error: function(jqXHR, textStatus, errorThrown){
      printControllerErrorAoT(wid);
    }
  });
}

// UI 갱신 (토글/배경색/문구)
function updateControllerUIAoT(wid, isActive){
  let toggler = document.getElementById("ctrl_toggle_"+wid);
  let contDiv = document.getElementById("container-aotctrl-"+wid);
  let stateSpan = document.getElementById("text-controller-state-"+wid);
  if(!toggler || !contDiv || !stateSpan) return;

  contDiv.classList.remove("pause-background-aotctrl",
                           "active-background-aotctrl",
                           "inactive-background-aotctrl");

  if(isActive){
    toggler.checked = true;
    contDiv.classList.add("active-background-aotctrl");
    stateSpan.innerHTML = "작동중";
  } else {
    toggler.checked = false;
    contDiv.classList.add("inactive-background-aotctrl");
    stateSpan.innerHTML = "대기중";
  }
}

// 컨트롤러 On/Off
function setControllerStateAoT(dev_id, newState, wid){
  $.ajax({
    url: "/controller_activate_deactivate/"+dev_id+"/"+newState,
    type: "GET",
    success: function(res){
      // Toastr 메시지 제거됨
      // (원하면 console.log로 대체)
      console.log("Controller set success:", res);

      // 명령 후 재확인 (1회)
      getControllerStateAoT(wid, dev_id);
    },
    error: function(err){
      // (Toastr 메시지 제거)
      console.error("Controller set error:", err);

      // UI에 에러 표시
      printControllerErrorAoT(wid);
    }
  });
}

// ---------------------- 복원된 "주기적 상태 갱신" 로직 ----------------------
function repeatControllerStateAoT(wid, dev_id, refSec){
  // refresh_seconds <= 0이면 자동 갱신 X
  if(!refSec || refSec <= 0){
    console.log("[AoT Controller] Auto-refresh disabled for widget:", wid);
    return;
  }

  console.log("[AoT Controller] Auto-refresh every", refSec, "seconds (widget:", wid, ")");
  setInterval(function(){
    getControllerStateAoT(wid, dev_id);
  }, refSec * 1000);
}
""",

    # -------------------- JS READY --------------------
    'widget_dashboard_js_ready': """
$('.controller_onoff_chk').change(function(){
  let wid = this.id.split('_')[2];  // ctrl_toggle_{wid}
  let dev_id = $(this).attr('name');
  let isOn = $(this).is(':checked');

  if(!dev_id){
    console.log("No Controller ID found for widget:", wid);
    return;
  }

  // on => 'activate', off => 'deactivate'
  let action = isOn ? "activate" : "deactivate";
  setControllerStateAoT(dev_id, action, wid);
});
""",

    # -------------------- JS READY END --------------------
    'widget_dashboard_js_ready_end': """
$('#ctrl_toggle_{{each_widget.unique_id}}')
  .attr('name', '{{widget_options['controller']}}');

// 1) 위젯 로드 시, 현재 상태 1회 조회
getControllerStateAoT('{{each_widget.unique_id}}', '{{widget_options['controller']}}');

// 2) refresh_seconds가 0보다 크면 주기적으로 상태 확인
repeatControllerStateAoT(
  '{{each_widget.unique_id}}',
  '{{widget_options['controller']}}',
  {{widget_options['refresh_seconds']}}
);
"""
}

logger.info(
    "widget_AoT_controller.py: 주기적 상태 갱신(=refresh_seconds) 복원 + Toastr 제거 유지."
)