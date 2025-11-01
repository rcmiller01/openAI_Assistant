#!/bin/sh
# PostgreSQL backup script

set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${POSTGRES_DB}_${TIMESTAMP}.sql.gz"
KEEP_DAYS=${BACKUP_KEEP_DAYS:-7}

echo "Starting backup of database ${POSTGRES_DB}..."

# Create backup
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
  -h "${POSTGRES_HOST}" \
  -U "${POSTGRES_USER}" \
  -d "${POSTGRES_DB}" \
  --no-owner \
  --no-acl \
  | gzip > "${BACKUP_FILE}"

echo "Backup created: ${BACKUP_FILE}"

# Remove old backups
find "${BACKUP_DIR}" -name "backup_${POSTGRES_DB}_*.sql.gz" -mtime +${KEEP_DAYS} -delete

echo "Old backups removed (older than ${KEEP_DAYS} days)"
echo "Backup completed successfully"
