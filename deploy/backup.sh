#!/bin/sh
# Backup of the Docker setup: the database and the uploaded photos, into ./backups/ (older than 14 days are deleted).
# Run it from anywhere on the server:   sh deploy/backup.sh
# Every night (the owner's server, `crontab -e`):   30 3 * * *  sh /home/tickbron/tickbron/deploy/backup.sh
# Copy ./backups/ to ANOTHER machine or a cloud disk as well: a backup on the same server dies with the server.
# Getting a backup back: .ai/DEPLOY_DOCKER.md ("Restore").
set -eu
# A database dump holds personal data: only the owner may read what this script writes
umask 077

cd "$(dirname "$0")/.."
stamp=$(date +%Y%m%d-%H%M%S)
db="backups/db-$stamp.dump"
media="backups/media-$stamp.tar.gz"
mkdir -p backups

# Whatever way the script ends, a half-written backup must not stay and look like a good one
done_ok=0
trap '[ "$done_ok" = 1 ] || rm -f "$db" "$media" "backups/media-$stamp.tar"' EXIT

# The database: one file that pg_restore can read
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' > "$db"

# The uploaded photos. No pipe into gzip: /bin/sh has no pipefail, so a failed copy would be hidden by gzip's success
docker compose cp web:/app/media - > "backups/media-$stamp.tar"
gzip -f "backups/media-$stamp.tar"

# An empty file means something went wrong: do not keep it as if it were a backup
for file in "$db" "$media"; do
  if [ ! -s "$file" ]; then
    echo "Backup failed: $file is empty" >&2
    exit 1
  fi
done

# Only a finished backup may delete the old ones
done_ok=1
find backups -name 'db-*.dump' -mtime +14 -delete
find backups -name 'media-*.tar.gz' -mtime +14 -delete
echo "Backup done: $db and $media"
