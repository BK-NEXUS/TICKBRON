#!/bin/sh
# Backup of the Docker setup: the database and the uploaded photos, into ./backups/ (older than 14 days are deleted).
# Run it from anywhere on the server:   sh deploy/backup.sh
# Every night (the owner's server, `crontab -e`):   30 3 * * *  sh /home/tickbron/tickbron/deploy/backup.sh
# Copy ./backups/ to ANOTHER machine or a cloud disk as well: a backup on the same server dies with the server.
# Getting a backup back: .ai/DEPLOY_DOCKER.md ("Restore").
set -eu

cd "$(dirname "$0")/.."
stamp=$(date +%Y%m%d-%H%M%S)
mkdir -p backups

# The database: one file that pg_restore can read
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' > "backups/db-$stamp.dump"

# The uploaded photos
docker compose cp web:/app/media - | gzip > "backups/media-$stamp.tar.gz"

# An empty file means something went wrong: do not keep it as if it were a backup
for file in "backups/db-$stamp.dump" "backups/media-$stamp.tar.gz"; do
  if [ ! -s "$file" ]; then
    echo "Backup failed: $file is empty" >&2
    rm -f "$file"
    exit 1
  fi
done

find backups -name 'db-*.dump' -mtime +14 -delete
find backups -name 'media-*.tar.gz' -mtime +14 -delete
echo "Backup done: backups/db-$stamp.dump and backups/media-$stamp.tar.gz"
