# coding=utf-8
#
#  widget_AoT_gauge_angular.py - Angular Gauge dashboard widget (AoT 버전)

import json
import logging
import re

from flask import flash
from flask_babel import lazy_gettext

from looperget.utils.constraints_pass import constraints_pass_positive_value

logger = logging.getLogger(__name__)

def execute_at_creation(error, new_widget, dict_widget):
    """ 위젯 생성 시, preset_config에 따라 min/max/색상 등을 덮어쓰기 """
    custom_options_json = json.loads(new_widget.custom_options)

    # 1) preset_config 확인
    preset = custom_options_json.get('preset_config', 'custom')

    # 2) 사용자 정의 기본 컬러 리스트(예시)
    color_list = ["#8BC1C1", "#DAF2E6", "#F4D624", "#FEA60B", "#DF5353"]

    # 3) preset에 따라 min/max, 색상 배열 등 오버라이드
    if preset == 'temperature':
        custom_options_json['min'] = -5
        custom_options_json['max'] = 45

    elif preset == 'humidity':
        # 색상 배열 역순
        color_list = list(reversed(color_list))

    elif preset == 'vpd':
        # VPD: min=0, max=3
        custom_options_json['min'] = 0
        custom_options_json['max'] = 3

        # “stops”도 5개로 고정
        custom_options_json['stops'] = 5

        # 미리 vpd 전용 구간을 만들 수도 있음 (직접 지정 예시)
        # 예: [0~0.25], [0.25~0.5], [0.5~1.2], [1.2~2], [2~3]
        # 여기서 색상은 color_list를 이용
        # (사용자 입력 대신 “정해진” 구간을 쓰고 싶다면 아래처럼 고정)
        custom_options_json['range_colors'] = [
            f"0,0.25,{color_list[0]}",
            f"0.25,0.5,{color_list[1]}",
            f"0.5,1.2,{color_list[2]}",
            f"1.2,2,{color_list[3]}",
            f"2,3,{color_list[4]}",
        ]

    # 4) stops/min/max 값이 없으면 기본 설정
    if 'stops' not in custom_options_json or custom_options_json['stops'] < 2:
        custom_options_json['stops'] = 2
    if 'min' not in custom_options_json:
        custom_options_json['min'] = 0
    if 'max' not in custom_options_json:
        custom_options_json['max'] = 100

    # 5) 기존 로직으로 range_colors를 자동 생성
    #    (단, 이미 'range_colors'가 있다면 그대로 둘 수도 있음)
    if 'range_colors' not in custom_options_json:
        custom_options_json['range_colors'] = []
        stop = custom_options_json['min']
        maximum = custom_options_json['max']
        difference = float(maximum - stop)
        stop_size = difference / custom_options_json['stops']

        # 첫 구간
        custom_options_json['range_colors'].append(
            f"{stop},{stop + stop_size},{color_list[0]}"
        )
        # 나머지 구간
        for i in range(custom_options_json['stops'] - 1):
            stop += stop_size
            if i+1 < len(color_list):
                color = color_list[i+1]
            else:
                color = "#DF5353"  # 기본
            custom_options_json['range_colors'].append(
                f"{stop},{stop + stop_size},{color}"
            )

    new_widget.custom_options = json.dumps(custom_options_json)
    return error, new_widget


def execute_at_modification(
        mod_widget,
        request_form,
        custom_options_json_presave,
        custom_options_json_postsave):
    allow_saving = True
    page_refresh = True
    error = []

    # 사용자가 제출한 color range 폼 파싱 ( “구간 끝” 없이 )
    sorted_colors, error = custom_colors_gauge(request_form, error)

    # gauge_reformat_stops() 기존 로직 적용
    sorted_colors = gauge_reformat_stops(
        custom_options_json_presave['stops'],
        custom_options_json_postsave['stops'],
        current_colors=sorted_colors)

    # ★ “구간 끝”을 자동으로 채우는 처리
    sorted_colors = fill_missing_highs(custom_options_json_postsave, sorted_colors)

    custom_options_json_postsave['range_colors'] = sorted_colors
    return allow_saving, page_refresh, mod_widget, custom_options_json_postsave

def generate_page_variables(widget_unique_id, widget_options):
    # Retrieve custom colors for gauges
    colors_gauge_angular = []
    try:
        if 'range_colors' in widget_options and widget_options['range_colors']:
            color_areas = widget_options['range_colors']
        else:
            color_areas = []

        for each_range in color_areas:
            colors_gauge_angular.append({
                'low': each_range.split(',')[0],
                'high': each_range.split(',')[1],
                'hex': each_range.split(',')[2]})
    except IndexError:
        logger.exception(1)
        flash("Colors Index Error", "error")

    return {"colors_gauge_angular": colors_gauge_angular}


WIDGET_INFORMATION = {
    'widget_name_unique': 'AoT_gauge_angular',
    'widget_name': 'AoT 원형 게이지',
    'widget_library': 'Highcharts',
    'no_class': True,

    # 위젯 설명 (한글화)
    'message': '원형(Angular) 게이지를 표시합니다. 게이지가 올바르게 표시되도록 최대값 옵션을 마지막 구간(High)에 맞춰 설정하세요.',

    'execute_at_creation': execute_at_creation,
    'execute_at_modification': execute_at_modification,
    'generate_page_variables': generate_page_variables,

    'widget_width': 5,
    'widget_height': 10,

    # 커스텀 옵션 (한글화, Stops 기본값 5로 변경)
    'custom_options': [
        {
            'id': 'measurement',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Function',
                'PID'
            ],
            'name': lazy_gettext('측정값'),
            'phrase': lazy_gettext('표시할 측정값을 선택하세요')
        },
        {
            'id': 'max_measure_age',
            'type': 'integer',
            'default_value': 1800,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{} ({})".format(lazy_gettext('최대 유효 시간'), lazy_gettext('초')),
            'phrase': lazy_gettext('해당 측정값의 최대 유효 시간을 설정하세요')
        },
        {
            'id': 'refresh_seconds',
            'type': 'float',
            'default_value': 30.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': '{} ({})'.format(lazy_gettext("새로고침"), lazy_gettext("초")),
            'phrase': '위젯을 새로고침할 주기를 설정하세요'
        },
        {
            'id': 'decimal_places',
            'type': 'integer',
            'default_value': 1,
            'name': '소수점 자릿수',
            'phrase': '소수점 이하 표시 자릿수를 설정하세요'
        },
        {
            'id': 'min',
            'type': 'float',
            'default_value': 0,
            'name': '최소값',
            'phrase': '게이지의 최소값을 설정하세요'
        },
        {
            'id': 'max',
            'type': 'float',
            'default_value': 100,
            'name': '최대값',
            'phrase': '게이지의 최대값을 설정하세요'
        },
        {
            'id': 'stops',
            'type': 'integer',
            'default_value': 5,  # 4 → 5로 변경
            'name': '색상 구간 수',
            'phrase': '게이지 색상을 구분할 구간 수를 설정하세요'
        },
        {
            'id': 'preset_config',
            'type': 'select',
            'default_value': 'custom',  # 기본: 사용자 정의
            'options_select': [
                ('custom', '사용자 정의'),
                ('temperature', '온도'),
                ('humidity', '습도'),
                ('vpd', 'VPD')
            ],
            'name': '사전 설정',
            'phrase': '사전 설정값을 선택하면, 최소/최대값 등 기본 설정이 자동으로 반영됩니다.'
        }
    ],

    'widget_dashboard_head': """{% if "highstock" not in dashboard_dict %}
  <script src="/static/js/user_js/highstock-9.1.2.js"></script>
  {% set _dummy = dashboard_dict.update({"highstock": 1}) %}
{% endif %}
<script src="/static/js/user_js/highcharts-more-9.1.2.js"></script>

{% if current_user.theme in dark_themes %}
  <script type="text/javascript" src="/static/js/dark-unica-custom.js"></script>
{% endif %}
""",

    'widget_dashboard_title_bar': """<span style="padding-right: 0.5em; font-size: {{each_widget.font_em_name}}em">{{each_widget.name}}</span>""",

    # 위젯 실제 표시 영역
    'widget_dashboard_body': """<div class="not-draggable" id="container-gauge-{{each_widget.unique_id}}" style="position: absolute; left: 0; top: 0; bottom: 0; right: 0; overflow: hidden;"></div>""",

    # 설정 화면에서 색상 구간 수정하는 부분
    # "구간 끝" 필드 완전히 제거. 구간 시작, 색상만 표시
    'widget_dashboard_configure_options': """
        {% for n in range(widget_variables['colors_gauge_angular']|length) %}
          {% set index = '{0:0>2}'.format(n) %}
        <div class="form-row">
          <div class="col-auto">
            <label class="control-label" for="color_low_number{{index}}">[{{n}}] 구간 시작</label>
            <div>
              <input class="form-control" id="color_low_number{{index}}" name="color_low_number{{index}}" type="text" value="{{widget_variables['colors_gauge_angular'][n]['low']}}">
            </div>
          </div>
          <div class="col-auto">
            <label class="control-label" for="color_hex_number{{index}}">[{{n}}] 색상</label>
            <div>
              <input id="color_hex_number{{index}}" name="color_hex_number{{index}}" placeholder="#000000" type="color" value="{{widget_variables['colors_gauge_angular'][n]['hex']}}">
            </div>
          </div>
        </div>
        {% endfor %}
    """,

    'widget_dashboard_js': """
  function getLastDataGaugeAngular(widget_id,
                       unique_id,
                       measure_type,
                       measurement_id,
                       max_measure_age_sec) {
    const url = '/last/' + unique_id + '/' + measure_type + '/' + measurement_id + '/' + max_measure_age_sec.toString();
    $.ajax(url, {
      success: function(data, responseText, jqXHR) {
        if (jqXHR.status === 204) {
          widget[widget_id].series[0].points[0].update(null);
        }
        else {
          const formattedTime = epoch_to_timestamp(data[0] * 1000);
          const measurement = data[1];
          widget[widget_id].series[0].points[0].update(measurement);
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        widget[widget_id].series[0].points[0].update(null);
      }
    });
  }

  // Repeat function for getLastDataGaugeAngular()
  function repeatLastDataGaugeAngular(widget_id,
                          dev_id,
                          measure_type,
                          measurement_id,
                          period_sec,
                          max_measure_age_sec) {
    setInterval(function () {
      getLastDataGaugeAngular(widget_id,
                  dev_id,
                  measure_type,
                  measurement_id,
                  max_measure_age_sec)
    }, period_sec * 1000);
  }
""",

    'widget_dashboard_js_ready': """<!-- No JS ready content -->""",

    'widget_dashboard_js_ready_end': """
{%- set device_id = widget_options['measurement'].split(",")[0] -%}
{%- set measurement_id = widget_options['measurement'].split(",")[1] -%}

{% set measure = { 'measurement_id': None } %}
  widget['{{each_widget.unique_id}}'] = new Highcharts.chart({
    chart: {
      renderTo: 'container-gauge-{{each_widget.unique_id}}',
      type: 'gauge',
      plotBackgroundColor: null,
      plotBackgroundImage: null,
      plotBorderWidth: 0,
      plotShadow: false,
      events: {
        load: function () {
          {% for each_input in input  if each_input.unique_id == device_id %}
          getLastDataGaugeAngular('{{each_widget.unique_id}}', '{{device_id}}', 'input', '{{measurement_id}}', {{widget_options['max_measure_age']}});
          repeatLastDataGaugeAngular('{{each_widget.unique_id}}', '{{device_id}}', 'input', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['max_measure_age']}});
          {%- endfor -%}
          
          {% for each_function in function if each_function.unique_id == device_id %}
          getLastDataGaugeAngular('{{each_widget.unique_id}}', '{{device_id}}', 'function', '{{measurement_id}}', {{widget_options['max_measure_age']}});
          repeatLastDataGaugeAngular('{{each_widget.unique_id}}', '{{device_id}}', 'function', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['max_measure_age']}});
          {%- endfor -%}

          {%- for each_pid in pid if each_pid.unique_id == device_id %}
          getLastDataGaugeAngular('{{each_widget.unique_id}}', '{{device_id}}', 'pid', '{{measurement_id}}', {{widget_options['max_measure_age']}});
          repeatLastDataGaugeAngular('{{each_widget.unique_id}}', '{{device_id}}', 'pid', '{{measurement_id}}', {{widget_options['refresh_seconds']}}, {{widget_options['max_measure_age']}});
          {%- endfor -%}
        }
      },
      spacingTop: 0,
      spacingLeft: 0,
      spacingRight: 0,
      spacingBottom: 0
    },

    title: null,

    exporting: {
      enabled: false
    },

    pane: {
        startAngle: -150,
        endAngle: 150,
        background: [{
            backgroundColor: '#c1c1c1',
            borderWidth: 0,
            outerRadius: '105%',
            innerRadius: '103%'
        }]
    },

    yAxis: {
        min: {{widget_options['min']}},
        max: {{widget_options['max']}},
        title: {
      {%- if measurement_id in dict_measure_units and
             dict_measure_units[measurement_id] in dict_units and
             dict_units[dict_measure_units[measurement_id]]['unit'] -%}
          text: '{{dict_units[dict_measure_units[measurement_id]]['unit']}}',
      {% else %}
          text: '',
      {%- endif -%}
          y: 20
        },

        minColor: "#3e3f46",
        maxColor: "#3e3f46",

        minorTickInterval: 'auto',
        minorTickWidth: 1,
        minorTickLength: 10,
        minorTickPosition: 'inside',
        minorTickColor: '#666',

        tickPixelInterval: 30,
        tickWidth: 2,
        tickPosition: 'inside',
        tickLength: 10,
        tickColor: '#666',
        labels: {
            step: 2,
            rotation: 'auto'
        },
        plotBands: [
          {% for n in range(widget_variables['colors_gauge_angular']|length) %}
            {% set index = '{0:0>2}'.format(n) %}
        {
            from: {{widget_variables['colors_gauge_angular'][n]['low']}},
            to: {{widget_variables['colors_gauge_angular'][n]['high']}},
            color: '{{widget_variables['colors_gauge_angular'][n]['hex']}}'
        },
          {% endfor %}
        ]
    },

    series: [{
        name: '
        {%- for each_input in input if each_input.unique_id == device_id -%}
          {%- if measurement_id in device_measurements_dict -%}
          {{each_input.name}} (
            {%- if not device_measurements_dict[measurement_id].single_channel -%}
              {{'CH' + (device_measurements_dict[measurement_id].channel|int)|string}}
            {%- endif -%}
            {%- if device_measurements_dict[measurement_id].measurement -%}
          {{', ' + dict_measurements[device_measurements_dict[measurement_id].measurement]['name']}}
            {%- endif -%}
          {%- endif -%}
        {%- endfor -%}
        
        {%- for each_function in function if each_function.unique_id == device_id -%}
          {{each_function.measure|safe}}
        {%- endfor -%}

        {%- for each_pid in pid if each_pid.unique_id == device_id -%}
          {{each_pid.measure|safe}}
        {%- endfor -%})',
        data: [null],
        dataLabels: {
          style: {"fontSize": "14px"},
          format: '{point.y:,.{{widget_options['decimal_places']}}f}'
        },
        yAxis: 0,
        dial: {
          backgroundColor: '{% if current_user.theme in dark_themes %}#e3e4f4{% else %}#3e3f46{% endif %}',
          baseWidth: 5
        },
        tooltip: {
        {%- for each_input in input if each_input.unique_id == device_id %}
             pointFormatter: function () {
              return this.series.name + ':<b> ' + Highcharts.numberFormat(this.y, 2) + ' {{dict_units[device_measurements_dict[measurement_id].unit]['unit']}}</b><br>';
            },
        {%- endfor -%}
            valueSuffix: '
        {%- for each_input in input if each_input.unique_id == device_id -%}
          {{' ' + dict_units[device_measurements_dict[measurement_id].unit]['unit']}}
        {%- endfor -%}
        
        {%- for each_function in function if each_function.unique_id == device_id -%}
          {{' ' + each_function.measure_units|safe}}
        {%- endfor -%}

        {%- for each_pid in pid if each_pid.unique_id == device_id -%}
          {{' ' + each_pid.measure_units|safe}}
        {%- endfor -%}'
        }
    }],

    credits: {
      enabled: false,
      href: "https://github.com/aot-inc/Looperget",
      text: "Looperget"
    }
  });
"""}


def is_rgb_color(color_hex):
    """
    Check if string is a valid 6-digit hex color (e.g. #FF0000)
    """
    return bool(re.compile(r'#[a-fA-F0-9]{6}$').match(color_hex))


############################
# “구간 끝” 제거 버전
############################
def custom_colors_gauge(form, error):
    """
    "구간 시작"(low), "색상"(hex)만 파싱한다. "구간 끝"(high)은 비워둔 채로 sorted_colors에 저장.
    """
    sorted_colors = []
    colors_hex = {}

    for key in form.keys():
        # "color_low_number##" / "color_hex_number##" 만 존재
        if 'color_low_number' in key or 'color_hex_number' in key:
            idx = int(key[16:])  # 예: color_low_number00 → 인덱스 00 → int(0)
            if idx not in colors_hex:
                colors_hex[idx] = {}

        if 'color_hex_number' in key:
            for value in form.getlist(key):
                if not is_rgb_color(value):
                    error.append('Invalid hex color value')
                colors_hex[idx]['hex'] = value

        elif 'color_low_number' in key:
            for value in form.getlist(key):
                colors_hex[idx]['low'] = value

    # 인덱스 순서대로 "low,,hex" 형태로 임시 저장
    for i in sorted(colors_hex.keys()):
        try:
            low_val = colors_hex[i].get('low', '0')
            hex_val = colors_hex[i].get('hex', '#000000')
            # middle(High)은 비워둠
            sorted_colors.append(f"{low_val},,{hex_val}")
        except Exception as err_msg:
            logger.exception(1)
            error.append(str(err_msg))

    return sorted_colors, error


def gauge_reformat_stops(current_stops, new_stops, current_colors=None):
    """기존 Looperget stops 로직. 구간 수가 늘거나 줄었을 때 colors를 맞춤."""
    if current_colors:
        colors = current_colors
    else:
        # 기본 예시 5개 색상 (신규 추가 시)
        colors = ['0,20,#8BC1C1', '20,40,#DAF2E6', '40,60,#F4D624', '60,80,#FEA60B', '80,100,#DF5353']

    if new_stops > current_stops:
        try:
            stop = float(colors[-1].split(",")[1])
        except:
            stop = 80
        for _ in range(new_stops - current_stops):
            stop += 20
            colors.append(f"{stop - 20},{stop},#DF5353")

    elif new_stops < current_stops:
        colors = colors[:len(colors) - (current_stops - new_stops)]

    return colors


def fill_missing_highs(custom_options_json, sorted_colors):
    """
    구간 전체에 대해,
    middle(High)이 비어 있는 경우 자동 계산:
    - 다음 구간의 Low → 현재 구간 High
    - 마지막 구간은 widget 'max' 값이 High
    """
    max_val = custom_options_json['max']

    for i in range(len(sorted_colors) - 1):
        low_i, high_i, color_i = sorted_colors[i].split(',')
        low_next, high_next, color_next = sorted_colors[i+1].split(',')

        # 현재 구간 High가 비어 있으면 다음 구간 Low를 대입
        if not high_i.strip():
            high_i = low_next
            sorted_colors[i] = f"{low_i},{high_i},{color_i}"

    # 마지막 구간 처리
    last_idx = len(sorted_colors) - 1
    low_last, high_last, color_last = sorted_colors[last_idx].split(',')
    if not high_last.strip():
        high_last = str(max_val)  # 마지막 구간 끝은 max
        sorted_colors[last_idx] = f"{low_last},{high_last},{color_last}"

    return sorted_colors