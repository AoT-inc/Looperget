#!/bin/bash
#
#  setup.sh - Looperget install script
#
#  Usage: sudo /bin/bash /opt/Looperget/install/setup.sh
#

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd -P )
INSTALL_CMD="/bin/bash ${INSTALL_DIRECTORY}/looperget/scripts/upgrade_commands.sh"
LOG_LOCATION=${INSTALL_DIRECTORY}/install/setup.log
UNAME_TYPE=$(uname -m)
MACHINE_TYPE=$(dpkg --print-architecture)
INFLUX_A='NONE'
INFLUX_B='NONE'

if [[ "$INSTALL_DIRECTORY" == "/opt/Looperget" ]]; then
  printf "## Currently installing with /opt/Looperget/install/setup.sh\n"
elif [[ "$INSTALL_DIRECTORY" != "/opt/Looperget" && ! -d /opt/Looperget ]]; then
  printf "## Current install directory (${INSTALL_DIRECTORY}) is not /opt/Looperget and /opt/Looperget doesn't exist. Copying and installing...\n"
  sudo cp -Rp "${INSTALL_DIRECTORY}" /opt/Looperget
  sudo /opt/Looperget/install/setup.sh
  exit 1
elif [[ "$INSTALL_DIRECTORY" != "/opt/Looperget" && -d /opt/Looperget ]]; then
  printf "## 에러: Install aborted. /opt/Looperget exists and you're running setup from ${INSTALL_DIRECTORY}. Install not possible if a previous install is detected. Move or delete /opt/Looperget and rerun this script or run /opt/Looperget/install/setup.sh\n"
  exit 1
fi

# Fix for below issue(s)
# https://github.com/pypa/setuptools/issues/3278
# https://github.com/aot-inc/Looperget/issues/1149
export SETUPTOOLS_USE_DISTUTILS=stdlib

if [ "$EUID" -ne 0 ]; then
    printf "Error: Script must be run as root, \"sudo /bin/bash %s/install/setup.sh\"\n" "${INSTALL_DIRECTORY}"
    exit 1
fi

printf "Checking Python version...\n"
if hash python3 2>/dev/null; then
  if ! python3 "${INSTALL_DIRECTORY}"/looperget/scripts/upgrade_check.py --min_python_version "3.6"; then
    printf "Error: Incorrect Python version found. Looperget requires Python >= 3.6.\n"
    exit 1
  else
    printf "Python >= 3.6 found.\n"
  fi
else
  printf "\nError: correct python version not found. Python >= 3.6 required in PATH to proceed with the install.\n"
  exit 1
fi

DIALOG=$(command -v dialog)
exitstatus=$?
if [ $exitstatus != 0 ]; then
    printf "\nError: dialog not installed. Install it then try the Looperget setup again.\n"
    exit 1
fi

START_A=$(date)
printf "### Looperge+ AI installation initiated %s\n" "${START_A}" 2>&1 | tee -a "${LOG_LOCATION}"

clear
LICENSE=$(dialog --title "Looperge+ AI Installer: License Agreement" \
                   --backtitle "Looperget" \
                   --yesno "Looperget is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.\n\nMycodo is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.\n\nYou should have received a copy of the GNU General Public License along with Looperget. If not, see gnu.org/licenses\n\nDo you agree to the license terms?" \
                   20 68 \
                   3>&1 1>&2 2>&3)

clear
LANGUAGE=$(dialog --title "Looperge+ AI Installer" \
                  --backtitle "Looperget" \
                  --menu "User Interface Language" 23 68 14 \
                  "en": "English" \
                  "ko": "한국어 (Korean)" \
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
    printf "Looperge+ AI install cancelled by user\n" 2>&1 | tee -a "${LOG_LOCATION}"
    exit 1
else
    echo "${LANGUAGE}" > "${INSTALL_DIRECTORY}/.language"
fi

clear
INSTALL=$(dialog --title "Looperge+ AI Installer: Install" \
                   --backtitle "Looperget" \
                   --yesno "Looperget will be installed in the home directory of the current user. Several software packages will be installed via apt, including the nginx web server that the Looperget web user interface will be hosted on. Proceed with the installation?" \
                   20 68 \
                   3>&1 1>&2 2>&3)
exitstatus=$?
if [ $exitstatus != 0 ]; then
    printf "Looperge+ AI install cancelled by user\n" 2>&1 | tee -a "${LOG_LOCATION}"
    exit 1
fi

clear
if [[ ${MACHINE_TYPE} == 'armhf' ]]; then
    INFLUX_A=$(dialog --title "Looperge+ AI Installer: Measurement Database" \
                        --backtitle "Looperget" \
                        --menu "Install Influxdb?\n\nIf you do not install InfluxDB now, you will need to set the InfluxDB server/credential settings in the Configuration after Looperget is installed." 20 68 4 \
                        "0)" "Install Influxdb 1.x (default)" \
                        "1)" "Do Not Install Influxdb" \
                        3>&1 1>&2 2>&3)
    exitstatus=$?
    if [ $exitstatus != 0 ]; then
        printf "Looperge+ AI install cancelled by user\n" 2>&1 | tee -a "${LOG_LOCATION}"
        exit 1
    fi
elif [[ ${MACHINE_TYPE} == 'arm64' || ${UNAME_TYPE} == 'x86_64' ]]; then
    INFLUX_B=$(dialog --title "Looperget Installer: Measurement Database" \
                        --backtitle "Looperget" \
                        --menu "Install Influxdb?\n\nIf you do not install InfluxDB now, you will need to configure the InfluxDB server settings and credentials after Looperget is installed. If using a 32-bit CPU, you can only use 1.x (do not use 2.x, as it only works with 64-bit CPUs)." 20 68 4 \
                        "0)" "Install Influxdb 2.x (recommended)" \
                        "1)" "Install Influxdb 1.x (old)" \
                        "2)" "Do Not Install Influxdb" \
                        3>&1 1>&2 2>&3)
    exitstatus=$?
    if [ $exitstatus != 0 ]; then
        printf "Looperge+ AI install cancelled by user\n" 2>&1 | tee -a "${LOG_LOCATION}"
        exit 1
    fi
else
    printf "\nError: Could not detect architecture\n"
    exit 1
fi

if [[ ${INFLUX_A} == '1)' || ${INFLUX_B} == '2)' ]]; then
    clear
    INSTALL=$(dialog --title "Looperge+ AI Installer: Measurement Database" \
                       --backtitle "Looperget" \
                       --yesno "You have chosen not to install Influxdb. This is typically done if you want to use an existing influxdb server. Make sure to change the influxdb client options in the Looperget Configuration after installing to ensure measurements can be properly saved/queried. If you would like to install influxdb, select cancel and start the Looperget Installer over again." \
                       20 68 \
                       3>&1 1>&2 2>&3)
    exitstatus=$?
    if [ $exitstatus != 0 ]; then
        printf "Looperge+ AI install cancelled by user\n" 2>&1 | tee -a "${LOG_LOCATION}"
        exit 1
    fi
fi

if [[ ${INFLUX_A} == 'NONE' && ${INFLUX_B} == 'NONE' ]]; then
    printf "\nError: Influx install option not selected\n"
    exit 1
fi

abort()
{
    printf "
****************************************
** ERROR During Looperge+ AI Install! **
****************************************

An error occurred that may have prevented Looperge+ AI 
from being installed properly!

Open to the end of the setup log to view the full error:
%s/install/setup.log

Please contact the developer by submitting a bug report
at https://github.com/AoT-inc/Looperget/issues with the
pertinent excerpts from the setup log located at:
%s/install/setup.log
" "${INSTALL_DIRECTORY}" "${INSTALL_DIRECTORY}" 2>&1 | tee -a "${LOG_LOCATION}"
    exit 1
}

trap 'abort' 0

set -e

clear
SECONDS=0
START_B=$(date)
printf "#### Looperge+ AI installation began %s\n" "${START_B}" 2>&1 | tee -a "${LOG_LOCATION}"

${INSTALL_CMD} update-swap-size 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-apt 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} uninstall-apt-pip 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-packages 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} setup-virtualenv 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-pip3 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} update-pip3-packages 2>&1 | tee -a "${LOG_LOCATION}"
${INSTALL_CMD} install-wiringpi 2>&1 | tee -a "${LOG_LOCATION}"
if [[ ${INFLUX_B} == '0)' ]]; then
    ${INSTALL_CMD} update-influxdb-2 2>&1 | tee -a "${LOG_LOCATION}"
    ${INSTALL_CMD} update-influxdb-2-db-user 2>&1 | tee -a "${LOG_LOCATION}"
elif [[ ${INFLUX_A} == '0)' || ${INFLUX_B} == '1)' ]]; then
    ${INSTALL_CMD} update-influxdb-1 2>&1 | tee -a "${LOG_LOCATION}"
    ${INSTALL_CMD} update-influxdb-1-db-user 2>&1 | tee -a "${LOG_LOCATION}"
elif [[ ${INFLUX_A} == '1)' || ${INFLUX_B} == '2)' ]]; then
    printf "Instructed to not install InfluxDB/n"
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
printf "#### Looperge+ AI Installer finished %s\n" "${END}" 2>&1 | tee -a "${LOG_LOCATION}"

DURATION=$SECONDS
printf "#### Total install time: %d minutes and %d seconds\n" "$((DURATION / 60))" "$((DURATION % 60))" 2>&1 | tee -a "${LOG_LOCATION}"

printf "
***************************************
** Looperge+ AI finished installing! **
***************************************

모든 설치가 완료되었습니다. 하지만 모든 설정이 완료된 것을 의미하지는 않습니다.
만약 어떠한 문제가 발생했다면, 아래의 로그를 확인해주세요:
%s/install/setup.log

다음 주소: https://${IP}/, 또는 무엇이든 장치의 IP 주소를 입력하여 
웹 브라우저에 입력하면 Looperge+ AI의 홈페이지로 이동할 수 있습니다.
관리자 계정을 생성하고 설정을 진행해주세요.
" "${INSTALL_DIRECTORY}" "${IP}" 2>&1 | tee -a "${LOG_LOCATION}"
