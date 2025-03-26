#!/bin/bash
#
#  setup.sh - Looperget 설치 스크립트
#
#  사용법: sudo /bin/bash /opt/Looperget/install/setup.sh
#

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd -P )
INSTALL_CMD="/bin/bash ${INSTALL_DIRECTORY}/looperget/scripts/upgrade_commands.sh"
LOG_LOCATION=${INSTALL_DIRECTORY}/install/setup.log
UNAME_TYPE=$(uname -m)
MACHINE_TYPE=$(dpkg --print-architecture)
INFLUX_A='NONE'
INFLUX_B='NONE'

if [[ "$INSTALL_DIRECTORY" == "/opt/Looperget" ]]; then
  printf "## 현재 /opt/Looperget/install/setup.sh로 설치 중입니다.\n"
elif [[ "$INSTALL_DIRECTORY" != "/opt/Looperget" && ! -d /opt/Looperget ]]; then
  printf "## 현재 설치 디렉터리 (${INSTALL_DIRECTORY})는 /opt/Looperget이 아니며 /opt/Looperget도 존재하지 않습니다. 복사 후 설치를 진행합니다...\n"
  sudo cp -Rp "${INSTALL_DIRECTORY}" /opt/Looperget
  sudo /opt/Looperget/install/setup.sh
  exit 1
elif [[ "$INSTALL_DIRECTORY" != "/opt/Looperget" && -d /opt/Looperget ]]; then
  printf "## 에러: 설치가 중단되었습니다. /opt/Looperget 디렉터리가 이미 존재하며, 현재 ${INSTALL_DIRECTORY}에서 설치를 진행 중입니다. 이전 설치가 감지되어 설치가 불가능합니다. /opt/Looperget을 이동하거나 삭제한 후, 스크립트를 다시 실행하십시오.\n"
  exit 1
fi

# https://github.com/pypa/setuptools/issues/3278 및 https://github.com/aot-inc/Looperget/issues/1149 참고
export SETUPTOOLS_USE_DISTUTILS=stdlib
export LANG=ko_KR.UTF-8
export LANGUAGE=ko_KR.UTF-8
export LC_ALL=ko_KR.UTF-8

if [ "$EUID" -ne 0 ]; then
    printf "에러: 스크립트는 루트 권한으로 실행되어야 합니다. \"sudo /bin/bash %s/install/setup.sh\" 명령으로 다시 실행하십시오.\n" "${INSTALL_DIRECTORY}"
    exit 1
fi

printf "Python 버전 확인 중...\n"
if hash python3 2>/dev/null; then
  if ! python3 "${INSTALL_DIRECTORY}"/looperget/scripts/upgrade_check.py --min_python_version "3.6"; then
    printf "에러: 잘못된 Python 버전이 감지되었습니다. Looperget은 Python 3.6 이상을 필요로 합니다.\n"
    exit 1
  else
    printf "Python 3.6 이상 확인됨.\n"
  fi
else
  printf "\n에러: 올바른 Python 버전을 찾을 수 없습니다. 설치를 진행하려면 PATH에 Python 3.6 이상이 필요합니다.\n"
  exit 1
fi

DIALOG=$(command -v dialog)
exitstatus=$?
if [ $exitstatus != 0 ]; then
    printf "\n에러: dialog가 설치되어 있지 않습니다. dialog를 설치한 후 Looperget 설치를 다시 시도하십시오.\n"
    exit 1
fi

START_A=$(date)
printf "### Looperge+ AI 설치 시작: %s\n" "${START_A}" 2>&1 | tee -a "${LOG_LOCATION}"

clear
LICENSE=$(dialog --title "Looperge+ AI 설치 프로그램: 라이선스 동의" \
                   --backtitle "Looperget" \
                   --yesno "Looperget은 자유 소프트웨어입니다. 사용자는 GNU 일반 공중 라이선스(GPL) 제3판(또는 선택에 따라 이후 버전)의 조건에 따라 소스코드를 재배포하거나 수정할 수 있습니다.
                    
이 소프트웨어는 유용하게 사용되기를 바라며 배포되었으나, 어떠한 보증도 제공하지 않습니다. (상품성이나 특정 목적에의 적합성에 대한 묵시적 보증 포함 없음)
자세한 내용은 GNU 일반 공중 라이선스를 참조하십시오.

Looperget+ AI와 함께 GNU 일반 공중 라이선스 사본이 제공되었어야 합니다. 없다면 gnu.org/licenses 를 확인하십시오.

라이선스 조건에 동의하십니까?" \
                   20 68 \
                   3>&1 1>&2 2>&3)

clear
LANGUAGE=$(dialog --title "Looperge+ AI 설치 프로그램" \
                  --backtitle "Looperget" \
                  --menu "사용자 인터페이스 언어 선택" 23 68 14 \
                  "ko": "한국어 (Korean)" \
                  "en": "English" \
                  "de": "Deutsche (German)" \
                  "es": "Español (Spanish)" \
                  "fr": "Français (French)" \
                  "it": "Italiano (Italian)" \
                  "nl": "Nederlands (Dutch)" \
                  "nn": "Norsk (Norwegian)" \
                  "pl": "Polski (Polish)" \
                  "pt": "Português (Portuguese)" \
                  "ru": "русский язык (Russian)" \
                  "sr": "српски (Serbian)" \
                  "sv": "Svenska (Swedish)" \
                  "tr": "Türkçe (Turkish)" \
                  "zh": "中文 (Chinese)" \
                  3>&1 1>&2 2>&3)
exitstatus=$?
if [ $exitstatus != 0 ]; then
    printf "Looperge+ AI 설치가 사용자에 의해 취소되었습니다.\n" 2>&1 | tee -a "${LOG_LOCATION}"
    exit 1
else
    echo "${LANGUAGE}" > "${INSTALL_DIRECTORY}/.language"
fi

clear
INSTALL=$(dialog --title "Looperge+ AI 설치 프로그램: 설치" \
                   --backtitle "Looperget" \
                   --yesno "Looperget은 현재 사용자의 홈 디렉터리에 설치됩니다. 또한, nginx 웹 서버 등 여러 소프트웨어 패키지가 apt를 통해 설치되며, Looperget 웹 사용자 인터페이스는 해당 서버에서 호스팅됩니다. 설치를 진행하시겠습니까?" \
                   20 68 \
                   3>&1 1>&2 2>&3)
exitstatus=$?
if [ $exitstatus != 0 ]; then
    printf "Looperge+ AI 설치가 사용자에 의해 취소되었습니다.\n" 2>&1 | tee -a "${LOG_LOCATION}"
    exit 1
fi

clear
if [[ ${MACHINE_TYPE} == 'armhf' ]]; then
    INFLUX_A=$(dialog --title "Looperge+ AI 설치 프로그램: 측정 데이터베이스" \
                        --backtitle "Looperget" \
                        --menu "InfluxDB를 설치하시겠습니까?\n\nInfluxDB를 설치하지 않으면, 설치 후 설정에서 InfluxDB 서버 및 자격 증명 설정을 직접 구성해야 합니다." 20 68 4 \
                        "0)" "InfluxDB 1.x 설치 (기본값)" \
                        "1)" "InfluxDB 설치 안 함" \
                        3>&1 1>&2 2>&3)
    exitstatus=$?
    if [ $exitstatus != 0 ]; then
        printf "Looperge+ AI 설치가 사용자에 의해 취소되었습니다.\n" 2>&1 | tee -a "${LOG_LOCATION}"
        exit 1
    fi
elif [[ ${MACHINE_TYPE} == 'arm64' || ${UNAME_TYPE} == 'x86_64' ]]; then
    INFLUX_B=$(dialog --title "Looperget 설치 프로그램: 측정 데이터베이스" \
                        --backtitle "Looperget" \
                        --menu "InfluxDB를 설치하시겠습니까?\n\n설치하지 않으면, 나중에 InfluxDB 서버 설정 및 자격 증명을 직접 구성해야 합니다. 32비트 CPU의 경우 InfluxDB 1.x만 사용 가능합니다 (2.x는 64비트 CPU 전용입니다)." 20 68 4 \
                        "0)" "InfluxDB 2.x 설치 (권장)" \
                        "1)" "InfluxDB 1.x 설치 (이전 버전)" \
                        "2)" "InfluxDB 설치 안 함" \
                        3>&1 1>&2 2>&3)
    exitstatus=$?
    if [ $exitstatus != 0 ]; then
        printf "Looperge+ AI 설치가 사용자에 의해 취소되었습니다.\n" 2>&1 | tee -a "${LOG_LOCATION}"
        exit 1
    fi
else
    printf "\n에러: 아키텍처를 감지할 수 없습니다.\n"
    exit 1
fi

if [[ ${INFLUX_A} == '1)' || ${INFLUX_B} == '2)' ]]; then
    clear
    INSTALL=$(dialog --title "Looperge+ AI 설치 프로그램: 측정 데이터베이스" \
                       --backtitle "Looperget" \
                       --yesno "InfluxDB 설치를 선택하지 않으셨습니다. 이는 기존 InfluxDB 서버를 사용할 경우에 해당합니다. 설치 후 Looperget 설정에서 InfluxDB 클라이언트 옵션을 변경하여 측정 데이터가 올바르게 저장/조회되도록 하십시오. InfluxDB를 설치하려면 취소를 선택한 후, 설치 프로그램을 다시 실행하십시오." \
                       20 68 \
                       3>&1 1>&2 2>&3)
    exitstatus=$?
    if [ $exitstatus != 0 ]; then
        printf "Looperge+ AI 설치가 사용자에 의해 취소되었습니다.\n" 2>&1 | tee -a "${LOG_LOCATION}"
        exit 1
    fi
fi

if [[ ${INFLUX_A} == 'NONE' && ${INFLUX_B} == 'NONE' ]]; then
    printf "\n에러: InfluxDB 설치 옵션이 선택되지 않았습니다.\n"
    exit 1
fi

abort()
{
    printf "
****************************************
** Looperge+ AI 설치 중 에러 발생! **
****************************************

설치가 올바르게 진행되지 않았을 수 있는 에러가 발생하였습니다.

전체 에러 메시지를 보려면 설치 로그 파일 끝부분을 확인하십시오:
%s/install/setup.log

문제가 지속된다면, 아래의 URL로 버그 리포트를 제출하여 개발자에게 연락해 주시기 바랍니다:
https://github.com/AoT-inc/Looperget/issues
설치 로그 (%s/install/setup.log)의 관련 부분을 함께 첨부해 주십시오.
" "${INSTALL_DIRECTORY}" "${INSTALL_DIRECTORY}" 2>&1 | tee -a "${LOG_LOCATION}"
    exit 1
}

trap 'abort' 0

set -e

clear
SECONDS=0
START_B=$(date)
printf "#### Looperge+ AI 설치 시작됨: %s\n" "${START_B}" 2>&1 | tee -a "${LOG_LOCATION}"

# (이후 설치 진행 관련 명령어는 동일하게 유지)

${INSTALL_CMD} update-swap-size 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-apt 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} uninstall-apt-pip 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-packages 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} setup-virtualenv 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-pip3 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-pip3-packages 2>&1 | tee -a "${LOG_LOCATION}"

if command -v npm >/dev/null 2>&1 && command -v zigbee2mqtt >/dev/null 2>&1; then
    printf "npm 및 zigbee2mqtt 이미 설치되어 있으므로, zigbee2mqtt 설치를 건너뜁니다.\n" 2>&1 | tee -a "${LOG_LOCATION}"
else
    printf "### zigbee2mqtt 시스템 서비스 설치 시작...\n" 2>&1 | tee -a "${LOG_LOCATION}"

    # Create the zigbee2mqtt service file and check for errors
    cat << 'EOF' > /etc/systemd/system/zigbee2mqtt.service || {
        printf "Error: zigbee2mqtt 서비스 파일 생성 실패\n" 2>&1 | tee -a "${LOG_LOCATION}"
        exit 1
    }

    [Unit]
    Description=zigbee2mqtt
    After=network.target

    [Service]
    ExecStart=/usr/bin/npm start
    WorkingDirectory=/opt/zigbee2mqtt
    StandardOutput=inherit
    StandardError=inherit
    Restart=always
    User=aot

    [Install]
    WantedBy=multi-user.target
    EOF

    if [ $? -ne 0 ]; then
        printf "Error: zigbee2mqtt 서비스 파일 작성에 실패하였습니다.\n" 2>&1 | tee -a "${LOG_LOCATION}"
        exit 1
    fi

    systemctl daemon-reload 2>&1 | tee -a "${LOG_LOCATION}" || {
        printf "Error: systemctl daemon-reload 실패\n" 2>&1 | tee -a "${LOG_LOCATION}"
        exit 1
    }

    systemctl enable zigbee2mqtt 2>&1 | tee -a "${LOG_LOCATION}" || {
        printf "Error: zigbee2mqtt 서비스 활성화 실패\n" 2>&1 | tee -a "${LOG_LOCATION}"
        exit 1
    }

    printf "### zigbee2mqtt 시스템 서비스 설치 완료.\n" 2>&1 | tee -a "${LOG_LOCATION}"
fi

${INSTALL_CMD} install-wiringpi 2>&1 | tee -a "${LOG_LOCATION}"
if [[ ${INFLUX_B} == '0)' ]]; then
    ${INSTALL_CMD} update-influxdb-2 2>&1 | tee -a "${LOG_LOCATION}"
    ${INSTALL_CMD} update-influxdb-2-db-user 2>&1 | tee -a "${LOG_LOCATION}"
elif [[ ${INFLUX_A} == '0)' || ${INFLUX_B} == '1)' ]]; then
    ${INSTALL_CMD} update-influxdb-1 2>&1 | tee -a "${LOG_LOCATION}"
    ${INSTALL_CMD} update-influxdb-1-db-user 2>&1 | tee -a "${LOG_LOCATION}"
elif [[ ${INFLUX_A} == '1)' || ${INFLUX_B} == '2)' ]]; then
    printf "InfluxDB 설치를 건너뛰도록 선택되었습니다.\n"
fi
${INSTALL_CMD} initialize 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-logrotate 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} ssl-certs-generate 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-looperget-startup-script 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} compile-translations 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} generate-widget-html 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} initialize 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} web-server-update 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} web-server-restart 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} web-server-connect 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-permissions 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} restart-daemon 2>&1 | tee -a "${LOG_LOCATION}"

trap : 0

IP=$(ip addr | grep 'state UP' -A2 | tail -n1 | awk '{print $2}' | cut -f1  -d'/')

if [[ -z ${IP} ]]; then
  IP="your.IP.address.here"
fi

END=$(date)
printf "#### Looperge+ AI 설치 프로그램 종료: %s\n" "${END}" 2>&1 | tee -a "${LOG_LOCATION}"

DURATION=$SECONDS
printf "#### 총 설치 시간: %d분 %d초\n" "$((DURATION / 60))" "$((DURATION % 60))" 2>&1 | tee -a "${LOG_LOCATION}"

printf "
***************************************
** Looperge+ AI 설치 완료! **
***************************************

모든 설치가 완료되었습니다. 단, 모든 설정이 완료되었음을 의미하지는 않습니다.
문제가 발생할 경우 아래의 로그 파일을 확인하십시오:
%s/install/setup.log

웹 브라우저에서 https://%s/ 또는 장치의 IP 주소를 입력하여 Looperge+ AI 홈페이지에 접속한 후,
관리자 계정을 생성하고 추가 설정을 진행해 주십시오.
" "${INSTALL_DIRECTORY}" "${IP}" 2>&1 | tee -a "${LOG_LOCATION}"
