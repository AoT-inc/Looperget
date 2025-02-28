# coding=utf-8
import copy
import requests
import datetime
from flask_babel import lazy_gettext

from looperget.inputs.base_input import AbstractInput
from looperget.inputs.sensorutils import calculate_dewpoint

measurements_dict = {
    0: {'measurement': 'temperature', 'unit': 'C'},
    1: {'measurement': 'humidity', 'unit': 'percent'},
    2: {'measurement': 'pressure', 'unit': 'Pa'},
    3: {'measurement': 'dewpoint', 'unit': 'C'},
    4: {'measurement': 'speed', 'unit': 'm_s', 'name': '풍속'},
    5: {'measurement': 'direction', 'unit': 'bearing', 'name': '풍향'}
}

INPUT_INFORMATION = {
    'input_name_unique': 'AoT_weather_stn',
    'input_manufacturer': 'AoT_KMA',
    'input_name': '기상청 지점 데이터',
    'input_name_short': '기상청 지점',
    'measurements_name': 'Humidity/Temperature/Pressure/Wind',
    'measurements_dict': measurements_dict,
    'url_additional': 'https://apihub.kma.go.kr',
    'measurements_rescale': False,

    'message': '기상청 API 허브에서 무료 API 키를 발급받고 가까운 관측지점의 STN을 입력하세요.'
               '참고: 무료 API는 하루 20000회 호출이 가능하며, 1회 호출당 1개의 관측지점 데이터를 반환합니다.',

    'options_enabled': [
        'measurements_select',
        'period',
        'pre_output'
    ],

    'custom_options': [
        {
            'id': 'api_key',
            'type': 'text',
            'default_value': '',
            'required': True,
            'name': lazy_gettext('API Key'),
            'phrase': "The API Key for this service's API"
        },
        {
            'id': 'stn',
            'type': 'text',
            'default_value': '',
            'required': True,
            'name': lazy_gettext('stn'),
            'phrase': "The stn to acquire the weather data"
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that gets weather for a stn."""

    # NEW: 마지막으로 처리한 TM(정시)를 기록할 변수
    last_tm_processed = None

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.api_url = None
        self.api_key = None
        self.stn = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        """
        초기화 로직 (필요한 부분 없으면 비워둬도 됨).
        여기에 last_tm_processed를 None으로 명시 초기화해도 되지만,
        클래스 변수로 이미 선언했으므로 생략 가능.
        """
        pass

    def get_measurement(self):
        now = datetime.datetime.now()
        last_full_hour = now.replace(minute=0, second=0, microsecond=0)
        self.now_str = last_full_hour.strftime('%Y%m%d%H%M')

        if self.api_key and self.stn:
            self.api_url = (
                "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"
                f"?tm={self.now_str}&stn={self.stn}&help=0&authKey={self.api_key}"
            )
            self.logger.debug("URL: {}".format(self.api_url))
        else:
            self.logger.error("API키와 지점정보(stn)을 입력하세요.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        # NEW: 이미 처리한 TM인지 확인
        #      (현재 self.now_str와 last_tm_processed가 같다면, 재처리 X)
        if self.last_tm_processed == self.now_str:
            self.logger.info(
                f"Skipping measurement. Already processed TM={self.now_str}"
            )
            return  # 중복 자료 무시

        try:
            response = requests.get(self.api_url, timeout=60)
            response.raise_for_status()
            data_text = response.text
            self.logger.debug("KMA raw response:\n{}".format(data_text))
        except Exception as e:
            self.logger.error(f"Error acquiring weather information: {e}")
            return

        temperature = None
        humidity = None
        pressure = None
        wind_speed = None
        wind_deg = None

        lines = data_text.strip().split('\n')
        valid_data_found = False
        for line in lines:
            if line.startswith('#'):
                continue  # 주석 라인은 패스

            cols = line.split()
            if len(cols) < 46:
                # 열 개수 부족하면 스킵
                continue

            try:
                # 인덱스: WD=2, WS=3, PS=9, TA=11, HM=13 (예시)
                WD = float(cols[2])   # 풍향
                WS = float(cols[3])   # 풍속
                PS = float(cols[9])   # 해면기압
                TA = float(cols[11])  # 기온
                HM = float(cols[13])  # 상대습도

                temperature = TA
                humidity = HM
                pressure = PS
                wind_speed = WS
                wind_deg = WD

                valid_data_found = True
                break  # 한 줄만 파싱 후 종료

            except (ValueError, IndexError) as e:
                self.logger.error(f"파싱 오류(숫자 변환 실패 등): {e}")
                continue

        if not valid_data_found:
            self.logger.error("No valid data found in KMA response.")
            return

        # 압력 hPa -> Pa 변환
        if pressure is not None:
            pressure *= 100.0

        self.logger.debug(
            "Parsed -> "
            f"Temp: {temperature}, Hum: {humidity}, Press: {pressure}, "
            f"Wind Speed: {wind_speed}, Wind Deg: {wind_deg}"
        )

        if self.is_enabled(0) and temperature is not None:
            self.value_set(0, temperature)
        if self.is_enabled(1) and humidity is not None:
            self.value_set(1, humidity)
        if self.is_enabled(2) and pressure is not None:
            self.value_set(2, pressure)

        if self.is_enabled(3) and temperature is not None and humidity is not None:
            dew_point = calculate_dewpoint(temperature, humidity)
            self.value_set(3, dew_point)

        if self.is_enabled(4) and wind_speed is not None:
            self.value_set(4, wind_speed)
        if self.is_enabled(5) and wind_deg is not None:
            self.value_set(5, wind_deg)

        # NEW: 중복 처리 방지 위해 last_tm_processed 갱신
        self.last_tm_processed = self.now_str

        return self.return_dict