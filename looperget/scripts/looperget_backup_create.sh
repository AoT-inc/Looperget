#!/bin/bash

exec 2>&1

if [ "$EUID" -ne 0 ] ; then
    printf "Must be run as root.\n"
    exit 1
fi

INSTALL_DIRECTORY=$( cd -P /var/looperget-root/.. && pwd -P )

function error_found {
    date
    printf "\n#### ERROR ####"
    printf "\nThere was an error detected while creating the backup. Please review the log at /var/log/looperget/loopergetbackup.log"
    exit 1
}

CURRENT_VERSION=$("${INSTALL_DIRECTORY}"/Looperget/env/bin/python "${INSTALL_DIRECTORY}"/Looperget/looperget/utils/github_release_info.py -c 2>&1)
NOW=$(date +"%Y-%m-%d_%H-%M-%S")
TMP_DIR="/var/tmp/Looperget-backup-${NOW}-${CURRENT_VERSION}"
BACKUP_DIR="/var/Looperget-backups/Looperget-backup-${NOW}-${CURRENT_VERSION}"

printf "\n#### Create backup initiated %s ####\n" "${NOW}"

mkdir -p /var/Looperget-backups

printf "Backing up current Looperget from %s/Looperget to %s..." "${INSTALL_DIRECTORY}" "${TMP_DIR}"
if ! rsync -avq --exclude=cameras --exclude=env --exclude=.upgrade "${INSTALL_DIRECTORY}"/Looperget "${TMP_DIR}" ; then
    printf "Failed: Error while trying to back up current Looperget install from %s/Looperget to %s.\n" "${INSTALL_DIRECTORY}" "${BACKUP_DIR}"
    error_found
fi
printf "Done.\n"

printf "Moving %s/Looperget to %s..." "${TMP_DIR}" "${BACKUP_DIR}"
if ! mv "${TMP_DIR}"/Looperget "${BACKUP_DIR}" ; then
    printf "Failed: Error while trying to move %s/Looperget to %s.\n" "${TMP_DIR}" "${BACKUP_DIR}"
    error_found
fi
printf "Done.\n"

date
printf "Backup completed successfully without errors.\n"
