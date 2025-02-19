#!/bin/bash
#
# Generates all required Looperget files
#
# Includes:
#
# Looperget Manual
# API Docs (swager)
# Translations
#
# Requirements (for generate_manual_api.sh):
# sudo apt install npm
# sudo npm install -g redoc-cli
# sudo npm install -g npx

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )

"${INSTALL_DIRECTORY}"/env/bin/python "${INSTALL_DIRECTORY}"/looperget/scripts/generate_manual_inputs_by_measure.py
"${INSTALL_DIRECTORY}"/env/bin/python "${INSTALL_DIRECTORY}"/looperget/scripts/generate_manual_inputs.py
"${INSTALL_DIRECTORY}"/env/bin/python "${INSTALL_DIRECTORY}"/looperget/scripts/generate_manual_outputs.py
"${INSTALL_DIRECTORY}"/env/bin/python "${INSTALL_DIRECTORY}"/looperget/scripts/generate_manual_functions.py
"${INSTALL_DIRECTORY}"/env/bin/python "${INSTALL_DIRECTORY}"/looperget/scripts/generate_manual_widgets.py
/bin/bash "${INSTALL_DIRECTORY}"/looperget/scripts/generate_manual_api.sh
/bin/bash "${INSTALL_DIRECTORY}"/looperget/scripts/generate_translations_pybabel.sh

# Compile translations, generate .mo binary files
/bin/bash "${INSTALL_DIRECTORY}"/looperget/scripts/upgrade_commands.sh compile-translations

# After generating translations, generate translated docs
"${INSTALL_DIRECTORY}"/env/bin/python "${INSTALL_DIRECTORY}"/looperget/scripts/generate_doc_translations.py
