# coding=utf-8
#
# widget_AoT_timer.py (개선버전)
# 작성일: 2025.01.14
# 작성자: AoT Inc.

import logging
from flask_babel import lazy_gettext
from looperget.utils.constraints_pass import constraints_pass_positive_value

logger = logging.getLogger(__name__)

WIDGET_INFORMATION = {
    'widget_name_unique': 'AoT_timer',
    'widget_name': 'AoT 타이머',
    'widget_library': 'timer',
    'no_class': True,

    'message': (
        '타이머에 입력한 시간만큼 장치가 작동하고 꺼집니다.'
        '타이머 시간이 "0"이면 종료를 누를 때까지 연속 작동하고 작동한 시간을 표시합니다.'
        '* 주의: 리로드 하거나, 창을 빠져나가면 장치는 작동하지만 시간은 초기화 됩니다.'
    ),

    'widget_width': 24,
    'widget_height': 7,

    'custom_options': [
        {
            'id': 'output',
            'type': 'select_channel',
            'default_value': '',
            'options_select': [
                'Output_Channels',
            ],
            'name': lazy_gettext('Output'),
            'phrase': '제어할 Output 을 선택하세요.'
        },
        {
            'id': 'refresh_seconds',
            'type': 'float',
            'default_value': 3.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': '{} ({})'.format(lazy_gettext("동기화"), lazy_gettext("초")),
            'phrase': lazy_gettext('사용할 측정값의 최대 유효 시간')
        },
        {
            'id': 'enable_status',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('상태 표시'),
            'phrase': lazy_gettext('작동상태를 타이틀바에 문자로 표시 합니다.')
        },
        {
            'id': 'status_font_em',
            'type': 'float',
            'default_value': 1.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('상태 크기'),
            'phrase': '상태 표시의 문자 크기를 설정할 수 있습니다. (em)'
        },
        {
            'id': 'enable_timestamp',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('작동시간'),
            'phrase': lazy_gettext('작동시간을 표시 합니다.')
        },
        {
            'id': 'widget_name_font_em',
            'type': 'float',
            'default_value': 1.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('작동시간 글자 크기'),
            'phrase': '작동 소요 시간과 시작 시간의 글자 크기 설정 합니다. (em)'
        },
        {
            'id': 'enable_output_controls',
            'type': 'bool',
            'default_value': True,
            'name': lazy_gettext('타이머'),
            'phrase': lazy_gettext('타이머 기능을 활성 합니다.')
        },
        {
            'id': 'font_em_time_input',
            'type': 'float',
            'default_value': 1.2,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('시간입력창 크기'),
            'phrase': lazy_gettext('시간 입력창 문자 크기 설정 합니다. (em)')
        }
    ],

    # ------------------ HEAD (CSS) ------------------
    'widget_dashboard_head': """
    <style>
      input[type=number]::-webkit-inner-spin-button,
      input[type=number]::-webkit-outer-spin-button {
        -webkit-appearance: none;
      }
      .mobile-timer-widget-slim {
        display: flex;
        flex-direction: column;
        width: 100%;
        height: 100%;
        box-sizing: border-box;
        overflow: hidden;
        background-color: #E9E9E9; /* 초기 OFF=연한 분홍 */
        transition: background-color 0.3s;
      }
      .timer-header-row-slim {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.6em;
      }
      .timer-widget-name-slim {
        text-align: left;
        margin-left: 0.5em;
      }
      .pause-background-timer {
        background-color: #fff3cd!important;
      }
      .active-background-timer {
        background-color: #FFF9E3!important;
      }
      .inactive-background-timer {
        background-color: #E9E9E9!important;
      }
      .toggle-switch-timer {
        position: relative;
        display: inline-block;
        width: 3.2em;
        height: 2em;
        margin-top: 0.9em;
        margin-right: 0.5em;
        vertical-align: middle;
      }
      .toggle-switch-timer input {
        opacity: 0;
        width: 0;
        height: 0;
      }
      .slider-timer {
        position: absolute;
        cursor: pointer;
        top: 0; left: 0; right: 0; bottom: 0;
        border-radius: 2em;
        background-color: #929292; /* OFF=빨강 */
        transition: 0.3s;
      }
      .slider-timer:before {
        position: absolute;
        content: "";
        height: 1.6em;
        width: 1.6em;
        left: 0.2em;
        bottom: 0.2em;
        line-height: 2em;
        background-color: white;
        border-radius: 100%;
        transition: 0.3s;
      }
      .toggle-switch-timer input:checked + .slider-timer {
        background-color: #F4D624; /* ON=초록 */
      }
      .toggle-switch-timer input:checked + .slider-timer:before {
        transform: translateX(1.2em);
      }
      .timer-second-row-slim {
        display: flex;
        gap: 0.5em;
        align-items: center;
        justify-content: flex-end;
        transform: translateY(-0.3em);
      }
      .time-inputs-slim {
        display: flex;
        flex-direction: row;
        gap: 0.3em;
        align-items: center;
      }
      .time-input-slim {
        width: 2.4em;
        height: 1.7em;
        text-align: center;
        font-size: 1.2em;
      }
      .buttons-slim {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.3em;
      }
      .btn-slim {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: none;
        width: 3.2em;
        height: 2em;
        padding: 0 0.5em;
        margin: 0;
        line-height: normal;
        font-size: 1em;
        border-radius: 0.3em;
        cursor: pointer;
        text-align: center;
        transition: background-color 0.2s;
        background-color: #F4D624;
        color: #000;
      }
      .btn-slim:hover {
        background-color: #929292;
      }
      .btn-slim:disabled {
        background-color: gray !important;
        cursor: not-allowed;
      }
    </style>
    """,

    # ------------------ TITLE BAR ------------------
    'widget_dashboard_title_bar': """
    {%- if widget_options['enable_status'] -%}
      <span id="text-output-state-slim-{{each_widget.unique_id}}"></span>
    {%- else -%}
      <span style="display:none" id="text-output-state-slim-{{each_widget.unique_id}}"></span>
    {%- endif %}
    <span>{{ each_widget.name }}</span>
    """,

    # ------------------ BODY ------------------
    'widget_dashboard_body': """
    {%- set device_id = '' -%}
    {%- set channel_id = '' -%}
    {%- if widget_options['output'] and ',' in widget_options['output'] -%}
      {%- set device_id = widget_options['output'].split(',')[0] -%}
      {%- set channel_id = widget_options['output'].split(',')[1] -%}
    {%- endif -%}

    <div class="mobile-timer-widget-slim inactive-background-timer"
         id="container-output-slim-{{each_widget.unique_id}}">

      <div style="width:100%; height:100%; box-sizing:border-box; overflow:hidden;">

        <!-- 1행: Timestamp(좌), 토글(우) -->
        <div class="timer-header-row-slim">
          {%- if widget_options['enable_timestamp'] %}
            <span class="timer-widget-name-slim"
                  style="font-size:{{widget_options['widget_name_font_em']}}em;"
                  id="timestamp_slim_{{each_widget.unique_id}}">
            </span>
          {%- else %}
            <span style="display:none" id="timestamp_slim_{{each_widget.unique_id}}"></span>
          {%- endif %}

          <label class="toggle-switch-timer">
            <input type="checkbox" class="start_stop_chk_slim"
                   id="slim_start_stop_{{each_widget.unique_id}}">
            <span class="slider-timer"></span>
          </label>
        </div>

        <!-- 2행: 시간입력 + 버튼 -->
        <div class="timer-second-row-slim"
             style="{% if not widget_options['enable_output_controls'] %}display:none;{% endif %}">
          <div class="time-inputs-slim">
            <input id="timer_hh_slim_{{each_widget.unique_id}}"
                   type="number"
                   class="time-input-slim"
                   min="0" max="48"
                   value="0"
                   style="font-size:{{widget_options['font_em_time_input']}}em;">
            <input id="timer_mm_slim_{{each_widget.unique_id}}"
                   type="number"
                   class="time-input-slim"
                   min="0" max="59"
                   value="0"
                   style="font-size:{{widget_options['font_em_time_input']}}em;">
            <input id="timer_ss_slim_{{each_widget.unique_id}}"
                   type="number"
                   class="time-input-slim"
                   min="0" max="59"
                   value="0"
                   style="font-size:{{widget_options['font_em_time_input']}}em;">
          </div>
          <div class="buttons-slim">
            <input class="btn-slim" id="reset_time_slim_{{each_widget.unique_id}}"
                   type="button" value="재설정">
            <input class="btn-slim" id="plus5_slim_{{each_widget.unique_id}}"
                   type="button" value="+5분">
            <input class="btn-slim" id="plus10_slim_{{each_widget.unique_id}}"
                   type="button" value="+10분" style="margin-right: 0.5em;">
          </div>
        </div>
      </div>
    </div>
    """,

    # ------------------ JAVASCRIPT ------------------
    'widget_dashboard_js': """
    function modOutputOutput_slim(cmdStr, widget_id) {
      $.ajax({
        type: 'GET',
        url: '/output_mod/' + cmdStr,
        success: function(data) {
          // 기존 로직: 서버상태 재확인
          getGPIOStateOutput_slim(widget_id);
        },
        error: function(jqXHR, textStatus, errorThrown){
          console.log("Command error (slim):", errorThrown);
        }
      });
    }

    function getGPIOStateOutput_slim(widget_id){
      const chkElem = $('#slim_start_stop_'+widget_id);
      if(!chkElem.length) return;

      const devName = chkElem.attr('name');
      if(!devName) return;

      const dev_id = devName.split('/')[0];
      const ch_id  = devName.split('/')[1];

      const cont = $('#container-output-slim-'+widget_id);
      const txt  = $('#text-output-state-slim-'+widget_id);
      const url  = '/outputstate_unique_id/' + dev_id + '/' + ch_id;

      $.getJSON(url, function(state){
        if(state==='off'){
          // 서버 OFF → UI OFF
          chkElem.prop('checked', false);
          cont.removeClass()
              .addClass('mobile-timer-widget-slim inactive-background-timer');
          txt.text('(Inactive)');

          stopCountdown_slim(widget_id);
          stopTimestampInterval_aotTimerSlim(widget_id, false);

        } else if(state==='on'){
          // 서버 ON → UI ON
          chkElem.prop('checked', true);
          cont.removeClass()
              .addClass('mobile-timer-widget-slim active-background-timer');
          txt.text('(Active)');

          // 서버 ON이면, 타임스탬프 표시 시작
          startTimestampInterval_aotTimerSlim(widget_id);

        } else {
          cont.removeClass()
              .addClass('mobile-timer-widget-slim pause-background-timer');
          txt.text('(No Connection)');
          stopCountdown_slim(widget_id);
          stopTimestampInterval_aotTimerSlim(widget_id, true);
        }
      });
    }

    // ---- 개선 전: 항상 setInterval() 수행 -> 개선 후: 별도 함수화 + 조건부 실행 ----
    function initAutoRefreshTimer_slim(widget_id, refreshSec) {
      if (!refreshSec || refreshSec <= 0) {
        console.log("Auto-refresh disabled (refresh_seconds <= 0). widget_id=", widget_id);
        return;
      }
      console.log("Auto-refresh enabled every", refreshSec, "seconds. widget_id=", widget_id);

      setInterval(function(){
        getGPIOStateOutput_slim(widget_id);
      }, refreshSec * 1000);
    }

    // 타이머(카운트다운) 관련
    let countdownInterval_slim = {};
    let currentSec_slim        = {};

    function getTimeInputs_slim(widget_id){
      let hh = parseInt($('#timer_hh_slim_'+widget_id).val())||0;
      let mm = parseInt($('#timer_mm_slim_'+widget_id).val())||0;
      let ss = parseInt($('#timer_ss_slim_'+widget_id).val())||0;
      if(hh>48) hh=48;
      if(mm>59) mm=59;
      if(ss>59) ss=59;
      return (hh*3600 + mm*60 + ss);
    }

    function applyTimeInputs_slim(widget_id, totalSec){
      if(totalSec<0) totalSec=0;
      const hh = Math.floor(totalSec/3600);
      const mm = Math.floor((totalSec%3600)/60);
      const ss = totalSec%60;
      $('#timer_hh_slim_'+widget_id).val(hh);
      $('#timer_mm_slim_'+widget_id).val(mm);
      $('#timer_ss_slim_'+widget_id).val(ss);
    }

    function startCountdown_slim(widget_id){
      if(countdownInterval_slim[widget_id]) return; // 이미 동작중

      const totalSec = getTimeInputs_slim(widget_id);
      currentSec_slim[widget_id] = totalSec;

      lockTimeInputs_slim(widget_id, true);

      if(totalSec <= 0){
        // 0초면 무기한 (OFF 누르기 전까지)
        return;
      }

      countdownInterval_slim[widget_id] = setInterval(function(){
        if(currentSec_slim[widget_id] > 0){
          currentSec_slim[widget_id]--;
        }
        applyTimeInputs_slim(widget_id, currentSec_slim[widget_id]);

        if(currentSec_slim[widget_id] <= 0){
          clearInterval(countdownInterval_slim[widget_id]);
          countdownInterval_slim[widget_id] = null;

          // 서버 off
          let baseName = $('#slim_start_stop_'+widget_id).attr('name');
          if(baseName){
            let dev_id= baseName.split('/')[0];
            let ch_id= baseName.split('/')[1];
            let cmd= dev_id+'/'+ch_id+'/off/sec/0';
            modOutputOutput_slim(cmd, widget_id);
          }
        }
      }, 1000);
    }

    function stopCountdown_slim(widget_id){
      if(countdownInterval_slim[widget_id]){
        clearInterval(countdownInterval_slim[widget_id]);
        countdownInterval_slim[widget_id] = null;
      }
      lockTimeInputs_slim(widget_id, false);
    }

    function lockTimeInputs_slim(widget_id, isLock){
      $('#timer_hh_slim_'+widget_id).prop('readOnly', isLock);
      $('#timer_mm_slim_'+widget_id).prop('readOnly', isLock);
      $('#timer_ss_slim_'+widget_id).prop('readOnly', isLock);
      $('#reset_time_slim_'+widget_id).prop('disabled', isLock);
      $('#plus5_slim_'+widget_id).prop('disabled', isLock);
      $('#plus10_slim_'+widget_id).prop('disabled', isLock);
    }

    // Timestamp 관련
    let timestampInterval_slim  = {};
    let timestampStartSec_slim  = {};
    let timestampStartDate_slim = {};

    function formatHMS_aotTimerSlim(sec){
      if(sec<0) sec=0;
      const hh= Math.floor(sec/3600);
      const mm= Math.floor((sec%3600)/60);
      const ss= sec%60;
      return String(hh).padStart(2,'0') + ":" +
             String(mm).padStart(2,'0') + ":" +
             String(ss).padStart(2,'0');
    }

    function formatMD_HMS_aotTimerSlim(d){
      let M= d.getMonth()+1;
      let D= d.getDate();
      let h= d.getHours();
      let m= d.getMinutes();
      let s= d.getSeconds();
      return M+"/"+D+" "+String(h).padStart(2,'0')+":"+
             String(m).padStart(2,'0')+":"+String(s).padStart(2,'0');
    }

    function stopTimestampInterval_aotTimerSlim(widget_id, clearDisplay=true){
      if(timestampInterval_slim[widget_id]){
        clearInterval(timestampInterval_slim[widget_id]);
        timestampInterval_slim[widget_id] = null;
      }
      if(clearDisplay){
        $('#timestamp_slim_'+widget_id).text("");
      }
    }

    function startTimestampInterval_aotTimerSlim(widget_id){
      if(timestampInterval_slim[widget_id]) return;

      let nowDate= new Date();
      timestampStartDate_slim[widget_id] = nowDate;
      timestampStartSec_slim[widget_id]  = Math.floor(nowDate.getTime()/1000);

      updateTimestamp_aot(widget_id);
      timestampInterval_slim[widget_id] = setInterval(function(){
        updateTimestamp_aot(widget_id);
      }, 1000);
    }

    function updateTimestamp_aot(widget_id){
      let nowSec= Math.floor(new Date().getTime()/1000);
      let diff  = nowSec - timestampStartSec_slim[widget_id];
      let eStr  = formatHMS_aotTimerSlim(diff);
      let sStr  = formatMD_HMS_aotTimerSlim(timestampStartDate_slim[widget_id]);
      $('#timestamp_slim_'+widget_id).text(eStr + ", " + sStr);
    }
    """,

    # ------------------ JS READY ------------------
    'widget_dashboard_js_ready': """
    $('[id^="reset_time_slim_"]').click(function(){
      let wid= this.id.split('_')[3];
      $('#timer_hh_slim_'+wid).val(0);
      $('#timer_mm_slim_'+wid).val(0);
      $('#timer_ss_slim_'+wid).val(0);
    });

    $('[id^="plus5_slim_"]').click(function(){
      let wid= this.id.split('_')[2];
      let sec= getTimeInputs_slim(wid);
      sec += 5*60;
      if(sec>48*3600) sec=48*3600;
      applyTimeInputs_slim(wid, sec);
    });

    $('[id^="plus10_slim_"]').click(function(){
      let wid= this.id.split('_')[2];
      let sec= getTimeInputs_slim(wid);
      sec += 10*60;
      if(sec>48*3600) sec=48*3600;
      applyTimeInputs_slim(wid, sec);
    });

    /* 토글 버튼 (ON/OFF) */
    $('[id^="slim_start_stop_"]').change(function(){
      let wid  = this.id.split('_')[3];
      let isOn = $(this).is(':checked');
      let devNm= $(this).attr('name');
      if(!devNm) return;

      let dev_id= devNm.split('/')[0];
      let ch_id = devNm.split('/')[1];
      let totalSec = getTimeInputs_slim(wid);

      if(isOn){
        let cmd= dev_id+'/'+ch_id+'/on/sec/'+ totalSec;
        modOutputOutput_slim(cmd, wid);

        startCountdown_slim(wid);
        startTimestampInterval_aotTimerSlim(wid);

      } else {
        let cmd= dev_id+'/'+ch_id+'/off/sec/0';
        modOutputOutput_slim(cmd, wid);

        stopCountdown_slim(wid);
        stopTimestampInterval_aotTimerSlim(wid, false);
      }
    });
    """,

    # ------------------ JS READY END ------------------
    'widget_dashboard_js_ready_end': """
    {%- set device_id = '' -%}
    {%- set channel_id = '' -%}
    {%- if widget_options['output'] and ',' in widget_options['output'] -%}
      {%- set device_id = widget_options['output'].split(',')[0] -%}
      {%- set channel_id = widget_options['output'].split(',')[1] -%}
    {%- endif -%}

    {%- if device_id and channel_id -%}
      // 토글 name 속성 세팅
      $('#slim_start_stop_{{each_widget.unique_id}}')
        .attr('name', '{{device_id}}/{{channel_id}}');

      // 1) 로드 시 1회 상태 확인
      getGPIOStateOutput_slim('{{each_widget.unique_id}}');

      // 2) refresh_seconds 간격으로만 자동 갱신
      initAutoRefreshTimer_slim('{{each_widget.unique_id}}', {{widget_options['refresh_seconds']}});
    {%- else -%}
      // Output 미선택 시 로직 없음
    {%- endif %}
    """
}

logger.info("widget_AoT_timer.py: 개선 완료 - 기존 버튼 로직 유지, 로드 시 1회 + refresh_seconds 주기로만 서버 상태 확인, 추가 주기 로직 제거.")