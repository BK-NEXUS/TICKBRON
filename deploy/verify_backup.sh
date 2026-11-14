#!/bin/sh
# Proves that the copy outside the server can really be restored (run it by hand now and then, for example once a month):
# restic checks the repository, the newest copy is restored into a temporary folder, the photo archive must be a valid
# gzip file and PostgreSQL must be able to read the dump. Nothing on the server is changed.
#   sh deploy/verify_backup.sh
set -eu
umask 077

cd "$(dirname "$0")/.."
if [ ! -f deploy/offsite.env ]; then
  echo "Cannot verify: deploy/offsite.env is missing (see deploy/offsite.env.example)" >&2
  exit 1
fi
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

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

restic check >/dev/null
restic restore latest --tag tickbron --target "$work" >/dev/null

db=$(find "$work" -name 'db-*.dump' | head -n 1)
media=$(find "$work" -name 'media-*.tar.gz' | head -n 1)
if [ -z "$db" ] || [ -z "$media" ] || [ ! -s "$db" ] || [ ! -s "$media" ]; then
  echo "Verification failed: the newest copy has no database dump or no photo archive" >&2
  exit 1
fi
gzip -t "$media"
docker compose exec -T db pg_restore --list < "$db" >/dev/null

echo "Offsite backup verified: $(basename "$db") and $(basename "$media") can be read"
# .env is deliberately not in the backup (it holds the keys). Without SECRET_KEY and TWO_FACTOR_KEY a restored database
# cannot read the stored two-factor secrets, so a copy of .env must be kept elsewhere (password manager)
echo "Reminder: .env (SECRET_KEY, TWO_FACTOR_KEY) is NOT in this backup. Keep a separate copy in the password manager."
