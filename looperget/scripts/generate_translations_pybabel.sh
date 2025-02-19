#!/bin/bash
#
# Generates the Looperget translation .po files
#
# Requires: pybabel in virtualenv
#

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )
CURRENT_VERSION=$("${INSTALL_DIRECTORY}"/env/bin/python3 "${INSTALL_DIRECTORY}"/looperget/utils/github_release_info.py -c 2>&1)

INFO_ARGS=(
  --project "Looperget"
  --version "${CURRENT_VERSION}"
  --copyright "Kyle T. Gabriel"
  --msgid-bugs-address "looperget@aot-inc.com"
)

cd "${INSTALL_DIRECTORY}"/looperget || return

printf "\n#### Extracting translatable texts\n"

"${INSTALL_DIRECTORY}"/env/bin/pybabel extract "${INFO_ARGS[@]}" -s -F babel.cfg -k lazy_gettext -o looperget_flask/translations/messages.pot .

printf "\n#### Generating translations\n"

"${INSTALL_DIRECTORY}"/env/bin/pybabel update --ignore-obsolete --update-header-comment -i looperget_flask/translations/messages.pot -d looperget_flask/translations
