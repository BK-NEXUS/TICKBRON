#!/bin/sh
# Backup of the Docker setup: the database and the uploaded photos, into ./backups/ (older than 14 days are deleted).
# Run it from anywhere on the server:   sh deploy/backup.sh
# Every night (the owner's server, `crontab -e`):   30 3 * * *  sh /home/tickbron/tickbron/deploy/backup.sh
# A backup on the same server dies with the server, so the script also sends an encrypted copy to a place outside it
# when deploy/offsite.env exists (see deploy/offsite.env.example). Without that file only the local copy is made.
# Getting a backup back: .ai/DEPLOY_DOCKER.md ("Restore"). Moving to another server: .ai/MOVE_SERVER.md.
set -eu
# A database dump holds personal data: only the owner may read what this script writes
umask 077

cd "$(dirname "$0")/.."
stamp=$(date +%Y%m%d-%H%M%S)
db="backups/db-$stamp.dump"
media="backups/media-$stamp.tar.gz"
mkdir -p backups

# The optional settings of the outside copy and of the failure notice (plain KEY=value lines, written by the owner)
if [ -f deploy/offsite.env ]; then
  # The file is run as shell, so whoever can change it could run commands here: refuse it unless only its owner (this
  # user) can read or write it
  if [ -n "$(find deploy/offsite.env \( -perm -g=r -o -perm -g=w -o -perm -o=r -o -perm -o=w -o ! -user "$(id -un)" \) 2>/dev/null)" ]; then
    echo "Refused: deploy/offsite.env must belong to this user and be private (chmod 600 deploy/offsite.env)" >&2
    exit 1
  fi
  set -a
  # shellcheck disable=SC1091
  . deploy/offsite.env
  set +a
fi

# Tells the team on Telegram when a night's backup failed. The token goes to curl on standard input, never on the
# command line (where any user of the server could read it). A failing notice must not hide the real failure.
tell_team() {
  [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_ALERT_CHAT_ID:-}" ] || return 0
  printf 'url = "https://api.telegram.org/bot%s/sendMessage"\ndata-urlencode = "chat_id=%s"\ndata-urlencode = "text=TICKBRON: the nightly backup failed (%s). Check the server."\n' \
    "$TELEGRAM_BOT_TOKEN" "$TELEGRAM_ALERT_CHAT_ID" "$(hostname)" | curl -fsS -m 20 --config - >/dev/null 2>&1 || true
}

# Whatever way the script ends, a half-written backup must not stay and look like a good one
local_ok=0
all_ok=0
finish() {
  [ "$local_ok" = 1 ] || rm -f "$db" "$media" "backups/media-$stamp.tar"
  [ "$all_ok" = 1 ] || tell_team
}
trap finish EXIT

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

# Only a finished local backup may delete the old ones
local_ok=1
find backups -name 'db-*.dump' -mtime +14 -delete
find backups -name 'media-*.tar.gz' -mtime +14 -delete
echo "Backup done: $db and $media"

# The copy outside the server: encrypted and de-duplicated by restic, old copies thinned out as 14 daily, 8 weekly and
# 6 monthly (change KEEP_* in deploy/offsite.env). If this fails the local backup stays, but the run fails loudly.
if [ -n "${RESTIC_REPOSITORY:-}" ]; then
  if ! restic backup "$db" "$media" --tag tickbron >/dev/null; then
    echo "Backup failed: the offsite copy could not be made" >&2
    exit 1
  fi
  if ! restic forget --keep-daily "${KEEP_DAILY:-14}" --keep-weekly "${KEEP_WEEKLY:-8}" --keep-monthly "${KEEP_MONTHLY:-6}" --prune >/dev/null; then
    echo "Backup failed: the offsite copy was made but old copies could not be removed" >&2
    exit 1
  fi
  echo "Offsite copy done"
fi
all_ok=1
