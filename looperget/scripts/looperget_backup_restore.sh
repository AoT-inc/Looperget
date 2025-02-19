#!/bin/bash

exec 2>&1

if [ "$EUID" -ne 0 ] ; then
    printf "Must be run as root.\n"
    exit 1
fi

if [ ! -e "$1" ]; then
    echo "Directory does not exist"
    exit 1
elif [ ! -d "$1" ]; then
    echo "Input not a directory"
    exit 2
fi

INSTALL_DIRECTORY=$( cd -P /var/looperget-root/.. && pwd -P )
echo '1' > "${INSTALL_DIRECTORY}"/Looperget/.restore

function error_found {
    echo '2' > "${INSTALL_DIRECTORY}"/Looperget/.restore
    printf "\n\n"
    date
    printf "#### ERROR ####\n"
    printf "There was an error detected during the restore. Please review the log at /var/log/looperget/loopergetrestore.log"
    exit 1
}

CURRENT_VERSION=$("${INSTALL_DIRECTORY}"/Looperget/env/bin/python "${INSTALL_DIRECTORY}"/Looperget/looperget/utils/github_release_info.py -c 2>&1)
NOW=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_DIR="/var/Looperget-backups/Looperget-backup-${NOW}-${CURRENT_VERSION}"

printf "\n#### Restore of backup %s initiated %s ####\n" "$1" "$NOW"

printf "#### Stopping Daemon and HTTP server ####\n"
service looperget stop
sleep 2
apachectl stop

/bin/bash "${INSTALL_DIRECTORY}"/Looperget/looperget/scripts/upgrade_commands.sh initialize

/bin/bash "${INSTALL_DIRECTORY}"/Looperget/looperget/scripts/upgrade_commands.sh update-permissions

printf "\nBacking up current Looperget from %s/Looperget to %s..." "${INSTALL_DIRECTORY}" "${BACKUP_DIR}"
if ! mv "${INSTALL_DIRECTORY}"/Looperget "${BACKUP_DIR}" ; then
    printf "Failed: Error while trying to back up current Looperget install from %s/Looperget to %s.\n" "${INSTALL_DIRECTORY}" "${BACKUP_DIR}"
    error_found
fi
printf "Done.\n"

printf "\nRestoring Looperget from %s to %s/Looperget..." "$1" "${INSTALL_DIRECTORY}"
if ! mv "$1" "${INSTALL_DIRECTORY}"/Looperget ; then
    printf "Failed: Error while trying to restore Looperget backup from %s/Looperget to %s.\n" "${INSTALL_DIRECTORY}" "${BACKUP_DIR}"
    error_found
fi
printf "Done.\n"

if [ -d "${BACKUP_DIR}"/env ] ; then
    printf "Moving env directory..."
    if ! mv "${BACKUP_DIR}"/env "${INSTALL_DIRECTORY}"/Looperget ; then
        printf "Failed: Error while trying to move env directory.\n"
        error_found
    fi
    printf "Done.\n"
fi

if [ -d "${BACKUP_DIR}"/cameras ] ; then
    printf "Moving cameras directory..."
    if ! mv "${BACKUP_DIR}"/cameras "${INSTALL_DIRECTORY}"/Looperget/ ; then
        printf "Failed: Error while trying to move cameras directory.\n"
    fi
    printf "Done.\n"
fi

sleep 10

if ! "${INSTALL_DIRECTORY}"/Looperget/looperget/scripts/upgrade_commands.sh initialize ; then
  printf "Failed: Error while running initialization.\n"
  error_found
fi

if ! "${INSTALL_DIRECTORY}"/Looperget/looperget/scripts/upgrade_commands.sh update-permissions ; then
  printf "Failed: Error while setting permissions.\n"
  error_found
fi

printf "\n\nRunning post-restore script...\n"
if ! "${INSTALL_DIRECTORY}"/Looperget/looperget/scripts/upgrade_post.sh ; then
  printf "Failed: Error while running post-restore script.\n"
  error_found
fi
printf "Done.\n\n"

date
printf "Restore completed successfully without errors.\n"

echo '0' > "${INSTALL_DIRECTORY}"/Looperget/.restore
