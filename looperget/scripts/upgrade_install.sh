#!/bin/bash
# Upgrade from a previous release to this current release.
# Check currently-installed version for the ability to upgrade to this release version.

exec 2>&1

RELEASE_WIPE=$1

if [ "$EUID" -ne 0 ] ; then
  printf "Must be run as root.\n"
  exit 1
fi

runSelfUpgrade() {
  function error_found {
    echo '2' > "${INSTALL_DIRECTORY}"/Looperget/.upgrade
    printf "\n\n"
    printf "#### ERROR ####\n"
    printf "There was an error detected during the upgrade. Please review the log at /var/log/looperget/loopergetupgrade.log"
    exit 1
  }

  printf "\n#### Beginning Upgrade Stage 2 of 3 ####\n\n"
  TIMER_START_stage_two=$SECONDS

  printf "RELEASE_WIPE = %s\n" "$RELEASE_WIPE"

  CURRENT_LOOPERGET_DIRECTORY=$( cd -P /var/looperget-root && pwd -P )
  CURRENT_LOOPERGET_INSTALL_DIRECTORY=$( cd -P /var/looperget-root/.. && pwd -P )
  THIS_LOOPERGET_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd -P )
  NOW=$(date +"%Y-%m-%d_%H-%M-%S")

  if [ "$CURRENT_LOOPERGET_DIRECTORY" == "$THIS_LOOPERGET_DIRECTORY" ] ; then
    printf "Cannot perform upgrade to the Looperget instance already installed. Halting upgrade.\n"
    exit 1
  fi

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}" ] ; then
    printf "Found currently-installed version of Looperget. Checking version...\n"
    CURRENT_VERSION=$("${CURRENT_LOOPERGET_INSTALL_DIRECTORY}"/Looperget/env/bin/python3 "${CURRENT_LOOPERGET_INSTALL_DIRECTORY}"/Looperget/looperget/utils/github_release_info.py -c 2>&1)
    MAJOR=$(echo "$CURRENT_VERSION" | cut -d. -f1)
    MINOR=$(echo "$CURRENT_VERSION" | cut -d. -f2)
    REVISION=$(echo "$CURRENT_VERSION" | cut -d. -f3)
    if [ -z "$MAJOR" ] || [ -z "$MINOR" ] || [ -z "$REVISION" ] ; then
      printf "Could not determine Looperget version\n"
      exit 1
    else
      printf "Looperget version found installed: %s.%s.%s\n" "${MAJOR}" "${MINOR}" "${REVISION}"
    fi
  else
    printf "Could not find a current version of Looperget installed. Check the symlink /var/mycdo-root that is supposed to point to the install directory"
    exit 1
  fi

  ################################
  # Begin tests prior to upgrade #
  ################################

  printf "\n#### Beginning pre-upgrade checks ####\n\n"

  # Upgrade requires Python >= 3.8
  printf "Checking Python version...\n"
  if hash python3 2>/dev/null; then
    if ! python3 "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/scripts/upgrade_check.py --min_python_version "3.8"; then
      printf "Error: Incorrect Python version found. Looperget requires Python >= 3.8.\n"
      echo '0' > "${CURRENT_LOOPERGET_DIRECTORY}"/.upgrade
      exit 1
    else
      printf "Python >= 3.8 found. Continuing with the upgrade.\n"
    fi
  else
    printf "\nError: python3 binary required in PATH to proceed with the upgrade.\n"
    echo '0' > "${CURRENT_LOOPERGET_DIRECTORY}"/.upgrade
    exit 1
  fi

  # If upgrading from version 7 and Python >= 3.6 found (from previous check), upgrade without wiping database
  if [[ "$MAJOR" == 7 ]] && [[ "$RELEASE_WIPE" = true ]]; then
    printf "Your system was found to have Python >= 3.6 installed. Proceeding with upgrade without wiping database.\n"
    RELEASE_WIPE=false
  fi

  printf "All pre-upgrade checks passed. Proceeding with upgrade.\n\n"

  ##############################
  # End tests prior to upgrade #
  ##############################

  THIS_VERSION=$("${CURRENT_LOOPERGET_DIRECTORY}"/env/bin/python3 "${THIS_LOOPERGET_DIRECTORY}"/looperget/utils/github_release_info.py -c 2>&1)
  printf "Upgrading Looperget to version %s\n\n" "$THIS_VERSION"

  printf "Stopping the Looperget daemon..."
  if ! service looperget stop ; then
    printf "Error: Unable to stop the daemon. Continuing anyway...\n"
  fi
  printf "Done.\n"

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/env ] ; then
    printf "Moving env directory..."
    if ! mv "${CURRENT_LOOPERGET_DIRECTORY}"/env "${THIS_LOOPERGET_DIRECTORY}" ; then
      printf "Failed: Error while trying to move env directory.\n"
      error_found
    fi
    printf "Done.\n"
  fi

  printf "Copying databases..."
  if ! cp "${CURRENT_LOOPERGET_DIRECTORY}"/databases/*.db "${THIS_LOOPERGET_DIRECTORY}"/databases ; then
    printf "Failed: Error while trying to copy databases."
    error_found
  fi
  printf "Done.\n"

  if [ -f "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/config_override.py ] ; then
    printf "Copying config_override.py..."
    if ! cp "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/config_override.py "${THIS_LOOPERGET_DIRECTORY}"/looperget/ ; then
      printf "Failed: Error while trying to copy config_override.py."
    fi
    printf "Done.\n"
  fi

  printf "Copying flask_secret_key..."
  if ! cp "${CURRENT_LOOPERGET_DIRECTORY}"/databases/flask_secret_key "${THIS_LOOPERGET_DIRECTORY}"/databases ; then
    printf "Failed: Error while trying to copy flask_secret_key."
  fi
  printf "Done.\n"

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/looperget_flask/ssl_certs ] ; then
    printf "Copying SSL certificates..."
    if ! cp -R "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/looperget_flask/ssl_certs "${THIS_LOOPERGET_DIRECTORY}"/looperget/looperget_flask/ssl_certs ; then
      printf "Failed: Error while trying to copy SSL certificates."
      error_found
    fi
    printf "Done.\n"
  fi

  # TODO: Remove in next major release
  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/controllers/custom_controllers ] ; then
    printf "Copying looperget/controllers/custom_controllers..."
    if ! cp "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/controllers/custom_controllers/*.py "${THIS_LOOPERGET_DIRECTORY}"/looperget/functions/custom_functions/ ; then
      printf "Failed: Error while trying to copy looperget/controllers/custom_controllers"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/functions/custom_functions ] ; then
    printf "Copying looperget/functions/custom_functions..."
    if ! cp "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/functions/custom_functions/*.py "${THIS_LOOPERGET_DIRECTORY}"/looperget/functions/custom_functions/ ; then
      printf "Failed: Error while trying to copy looperget/functions/custom_functions"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/actions/custom_actions ] ; then
    printf "Copying looperget/actions/custom_actions..."
    if ! cp "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/actions/custom_actions/*.py "${THIS_LOOPERGET_DIRECTORY}"/looperget/actions/custom_actions/ ; then
      printf "Failed: Error while trying to copy looperget/actions/custom_actions"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/inputs/custom_inputs ] ; then
    printf "Copying looperget/inputs/custom_inputs..."
    if ! cp "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/inputs/custom_inputs/*.py "${THIS_LOOPERGET_DIRECTORY}"/looperget/inputs/custom_inputs/ ; then
      printf "Failed: Error while trying to copy looperget/inputs/custom_inputs"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/outputs/custom_outputs ] ; then
    printf "Copying looperget/outputs/custom_outputs..."
    if ! cp "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/outputs/custom_outputs/*.py "${THIS_LOOPERGET_DIRECTORY}"/looperget/outputs/custom_outputs/ ; then
      printf "Failed: Error while trying to copy looperget/outputs/custom_outputs"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/widgets/custom_widgets ] ; then
    printf "Copying looperget/widgets/custom_widgets..."
    if ! cp "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/widgets/custom_widgets/*.py "${THIS_LOOPERGET_DIRECTORY}"/looperget/widgets/custom_widgets/ ; then
      printf "Failed: Error while trying to copy looperget/widgets/custom_widgets"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/user_python_code ] ; then
    printf "Copying looperget/user_python_code..."
    if ! cp "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/user_python_code/*.py "${THIS_LOOPERGET_DIRECTORY}"/looperget/user_python_code/ ; then
      printf "Failed: Error while trying to copy looperget/user_python_code"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/note_attachments ] ; then
    printf "Copying looperget/note_attachments..."
    if ! cp -r "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/note_attachments "${THIS_LOOPERGET_DIRECTORY}"/looperget/ ; then
      printf "Failed: Error while trying to copy looperget/note_attachments"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/looperget_flask/static/js/user_js ] ; then
    printf "Copying looperget/looperget_flask/static/js/user_js..."
    if ! cp -r "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/looperget_flask/static/js/user_js "${THIS_LOOPERGET_DIRECTORY}"/looperget/looperget_flask/static/js/ ; then
      printf "Failed: Error while trying to copy looperget/looperget_flask/static/js/user_js"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/looperget_flask/static/css/user_css ] ; then
    printf "Copying looperget/looperget_flask/static/css/user_css..."
    if ! cp -r "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/looperget_flask/static/css/user_css "${THIS_LOOPERGET_DIRECTORY}"/looperget/looperget_flask/static/css/ ; then
      printf "Failed: Error while trying to copy looperget/looperget_flask/static/css/user_css"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/looperget_flask/static/fonts/user_fonts ] ; then
    printf "Copying looperget/looperget_flask/static/fonts/user_fonts..."
    if ! cp -r "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/looperget_flask/static/fonts/user_fonts "${THIS_LOOPERGET_DIRECTORY}"/looperget/looperget_flask/static/fonts/ ; then
      printf "Failed: Error while trying to copy looperget/looperget_flask/static/fonts/user_fonts"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/user_scripts ] ; then
    printf "Copying looperget/user_scripts..."
    if ! cp -r "${CURRENT_LOOPERGET_DIRECTORY}"/looperget/user_scripts "${THIS_LOOPERGET_DIRECTORY}"/looperget/ ; then
      printf "Failed: Error while trying to copy looperget/user_scripts"
      error_found
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/output_usage_reports ] ; then
    printf "Moving output_usage_reports directory..."
    if ! mv "${CURRENT_LOOPERGET_DIRECTORY}"/output_usage_reports "${THIS_LOOPERGET_DIRECTORY}" ; then
      printf "Failed: Error while trying to move output_usage_reports directory.\n"
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/cameras ] ; then
    printf "Moving cameras directory..."
    if ! mv "${CURRENT_LOOPERGET_DIRECTORY}"/cameras "${THIS_LOOPERGET_DIRECTORY}" ; then
      printf "Failed: Error while trying to move cameras directory.\n"
    fi
    printf "Done.\n"
  fi

  if [ -d "${CURRENT_LOOPERGET_DIRECTORY}"/.upgrade ] ; then
    printf "Moving .upgrade file..."
    if ! mv "${CURRENT_LOOPERGET_DIRECTORY}"/.upgrade "${THIS_LOOPERGET_DIRECTORY}" ; then
      printf "Failed: Error while trying to move .upgrade file.\n"
    fi
    printf "Done.\n"
  fi

  if [ ! -d "/var/Looperget-backups" ] ; then
    mkdir /var/Looperget-backups
  fi

  BACKUP_DIR="/var/Looperget-backups/Looperget-backup-${NOW}-${CURRENT_VERSION}"

  printf "Moving current Looperget install from %s to %s..." "${CURRENT_LOOPERGET_DIRECTORY}" "${BACKUP_DIR}"
  if ! mv "${CURRENT_LOOPERGET_DIRECTORY}" "${BACKUP_DIR}" ; then
    printf "Failed: Error while trying to move old Looperget install from %s to %s.\n" "${CURRENT_LOOPERGET_DIRECTORY}" "${BACKUP_DIR}"
    error_found
  fi
  printf "Done.\n"

  mkdir -p /opt

  printf "Moving downloaded Looperget version from %s to /opt/Looperget..." "${THIS_LOOPERGET_DIRECTORY}"
  if ! mv "${THIS_LOOPERGET_DIRECTORY}" /opt/Looperget ; then
    printf "Failed: Error while trying to move new Looperget install from %s to /opt/Looperget.\n" "${THIS_LOOPERGET_DIRECTORY}"
    error_found
  fi
  printf "Done.\n"

  sleep 30

  cd /opt/Looperget || return

  ############################################
  # Begin tests prior to post-upgrade script #
  ############################################

  if [ "$RELEASE_WIPE" = true ] ; then
    # Instructed to wipe configuration files (database, virtualenv)

    if [ -d /opt/Looperget/env ] ; then
      printf "Removing virtualenv at /opt/Looperget/env..."
      if ! rm -rf /opt/Looperget/env ; then
        printf "Failed: Error while trying to delete virtaulenv at /opt/Looperget/env.\n"
      fi
      printf "Done.\n"
    fi

    if [ -d /opt/Looperget/databases/looperget.db ] ; then
      printf "Removing database at /opt/Looperget/databases/looperget.db..."
      if ! rm -f /opt/Looperget/databases/looperget.db ; then
        printf "Failed: Error while trying to delete database at /opt/Looperget/databases/looperget.db.\n"
      fi
      printf "Done.\n"
    fi

  fi

  printf "\n#### Completed Upgrade Stage 2 of 3 in %s seconds ####\n" "$((SECONDS - TIMER_START_stage_two))"

  ##########################################
  # End tests prior to post-upgrade script #
  ##########################################

  printf "\n#### Beginning Upgrade Stage 3 of 3 ####\n\n"
  TIMER_START_stage_three=$SECONDS

  printf "Running post-upgrade script...\n"
  if ! /opt/Looperget/looperget/scripts/upgrade_post.sh ; then
    printf "Failed: Error while running post-upgrade script.\n"
    error_found
  fi

  printf "\n#### Completed Upgrade Stage 3 of 3 in %s seconds ####\n\n" "$((SECONDS - TIMER_START_stage_three))"

  printf "Upgrade completed. Review the log to ensure no critical errors were encountered\n"

  #############################
  # Begin tests after upgrade #
  #############################



  ###########################
  # End tests after upgrade #
  ###########################

  echo '0' > /opt/Looperget/.upgrade

  exit 0
}

runSelfUpgrade
