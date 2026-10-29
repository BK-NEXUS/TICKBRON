# Putting TICKBRON on a server with Docker

This is the step-by-step for one Linux server (the owner's own server, a rented VPS or an AWS EC2 machine: the steps are the same). Every step says how to check it worked. The files: `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `deploy/Caddyfile`, `deploy/docker.env.example`, `deploy/backup.sh`.

## What runs

| Container | What it does | Open to the internet |
|---|---|---|
| `caddy` | The web server: the site, `/api/`, the photos; gets the HTTPS certificate by itself | yes, ports 80 and 443 |
| `web` | The API (Django, gunicorn) | no |
| `worker` | Background tasks: e-mails, Telegram notices, exchange rates | no |
| `beat` | The scheduler (exchange rates twice a day). Exactly one copy, never scale it | no |
| `migrate` | Runs once at every start: applies new database changes, then stops | no |
| `db` | PostgreSQL 16 (data in the `pgdata` volume) | no |
| `redis` | Redis (cache, throttles, the task queue; `redisdata` volume) | no |

Data that must survive: the volumes `pgdata` (database), `media` (uploaded photos) and `caddy_data` (HTTPS certificates). Stopping or rebuilding containers does not touch them; `docker compose down -v` DELETES them: never type that on the real server.

## What you need

- A Linux server, Ubuntu 22.04 or 24.04, at least 2 CPU, 4 GB RAM (2 GB works for a start), 40 GB disk, and a user with `sudo`.
- The domain with a DNS record pointing at the server (step 1).
- Mail settings (SMTP host, user, password) from any mail service, for password reset and notices.
- The code on the server (step 3).

## Step 1. The domain (ahost.uz)

In the domain's DNS panel add two **A** records, both with the server's public IP address:
- `@` (the bare name `tickbron.com`)
- `www`

Check, from your own computer (it can take from minutes up to a few hours): `nslookup tickbron.com` must show the server's IP. Do this before step 5: the certificate can only be issued when the name already points at the server.

### IPv6 (optional, later)

The site works with IPv4 only, which every visitor can reach. IPv6 is an extra: add an **AAAA** record (`@` and `www`) with the server's public IPv6 address **only after** this check passes, because Docker can hide the visitor's real address behind its own:

1. Visit the site over IPv6 only (for example `curl -6 https://tickbron.com/healthz/` from a computer with IPv6, or an online "IPv6 only" tester) with the AAAA record already set.
2. `docker compose logs caddy | tail`: the line of that request must show your real IPv6 address. If it shows a Docker address (`172.` or `fd00:`), remove the AAAA record again: every IPv6 visitor would then look like one visitor to the limits and the login lock.

What the app does by itself: it stores and shows IPv6 addresses (audit log, last login), and the limits (login, register, anonymous API, ad view counting, login lock) count an IPv6 visitor by its /64 block, because a provider gives one connection a whole block and the visitor can change address inside it. IPv4 is counted per address as before. Caddy needs no setting for IPv6.

## Step 2. Prepare the server

```
sudo apt update && sudo apt -y upgrade
sudo apt -y install ufw git
sudo ufw allow OpenSSH && sudo ufw allow 80/tcp && sudo ufw allow 443 && sudo ufw enable
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER      # log out and in again after this
docker compose version              # must print a version
```

The firewall lets in only SSH, 80 and 443. The database and Redis are not published on the server at all.

## Step 3. Get the code

Either `git clone <repository address> tickbron && cd tickbron` (the repository is private: use a deploy key or an access token), or copy the folder from your computer (`scp`/`rsync`). Everything below runs inside this folder.

## Step 4. Fill in the settings

```
cp deploy/docker.env.example .env
chmod 600 .env
nano .env
```

Change every value that says `CHANGE_ME`, and `DOMAIN`, `ALLOWED_HOSTS`, `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `DEFAULT_FROM_EMAIL` to the real domain. Make the secret key with:

```
docker compose run --rm --no-deps web python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

`.env` holds passwords: it is not in git, do not send it by chat or e-mail. The app refuses to start with a weak or missing setting and says which one (`docker compose logs migrate`).

## Step 5. Start

```
docker compose up -d --build
docker compose ps          # every line "Up", db/redis/web "(healthy)"; migrate is gone (it finished)
```

The first start builds the images (a few minutes). Then open `https://your-domain`: the site must load with a valid certificate. If not, see "Problems".

## Step 6. The first administrator

```
docker compose exec -e DJANGO_SUPERUSER_PASSWORD='a-long-password' web python manage.py createsuperuser --noinput --email you@your-domain
```

Then add the property types (hotel, hostel, guest house, apartment, resort). A new server has none, and an owner cannot add a hotel without one. Safe to run again:

```
docker compose exec web python manage.py seed_property_types
```

Sign in at `https://your-domain/login` with that e-mail. Hotel owner accounts are created by this administrator in the admin panel. Do NOT run `seed_demo` on the real server (it is for development and refuses to run without DEBUG).

## Update to a new version

```
sh deploy/backup.sh                 # always first
git pull
docker compose up -d --build        # new database changes are applied by `migrate` automatically
docker compose ps
```

## Backups

`sh deploy/backup.sh` writes the database and the photos into `backups/` and removes files older than 14 days. Run it every night:

```
crontab -e
30 3 * * *  sh /home/<user>/tickbron/deploy/backup.sh >> /home/<user>/backup.log 2>&1
```

A backup on the same server is lost with the server: copy `backups/` to another machine or a cloud disk every day too.

### Restore

```
# the database (from the file you choose)
docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' < backups/db-YYYYMMDD-HHMMSS.dump
# the photos
docker compose cp backups/media-YYYYMMDD-HHMMSS.tar.gz web:/tmp/m.tgz
docker compose exec -T web tar xzf /tmp/m.tgz -C /app
```

A restore was tried on a test copy of this setup (a deleted user came back, a deleted photo came back and was served again).

## Look at it

- `docker compose ps`: what runs and whether it is healthy.
- `docker compose logs -f web` (or `worker`, `beat`, `caddy`, `db`): what happens now; Ctrl+C leaves.
- `curl -s https://your-domain/api/v1/properties/search/ | head -c 200`: the API answers.

## Problems

- **The certificate is not issued / the browser warns**: the DNS name does not point at the server yet (step 1), or ports 80/443 are closed (step 2). `docker compose logs caddy` says which. Caddy retries by itself.
- **`migrate` or `web` stops at start**: `docker compose logs migrate` names the setting that is wrong or missing (the app checks its production settings).
- **400 "DisallowedHost" / the API refuses**: `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` or `CORS_ALLOWED_ORIGINS` in `.env` do not match the domain (they take the domain exactly, `https://` in the last two). After editing `.env`: `docker compose up -d`.
- **The site calls the wrong address**: the address of the API is built into the site. After changing `DOMAIN` run `docker compose up -d --build`.
- **No e-mails**: the SMTP values in `.env`; `docker compose logs worker` shows the errors.
- **Disk full**: `docker system df`; old images: `docker image prune`. Never `docker volume prune` on the real server.

## Security notes

- Only SSH, 80 and 443 are open. Use SSH keys, switch password login off, keep the server updated (`sudo apt install unattended-upgrades`).
- `.env` is `chmod 600` and only on the server. The images contain no secret (`.dockerignore`).
- The app runs as a normal user in its container, not as root.
- One server is one point of failure: the backups above are the way back. For two servers or automatic failover a different setup (for example Kubernetes or AWS ECS) is needed; the same images can be used.

## Trying it on a computer first

Set `DOMAIN=localhost`, `ALLOWED_HOSTS=localhost`, the three https:// addresses to `https://localhost:8443`, `HTTP_PORT=8080`, `HTTPS_PORT=8443` in `.env`, then `docker compose up -d --build` and open `https://localhost:8443` (the browser warns about the local certificate: that is expected here only).

## Known limits

- Not run on a real server with a real domain yet: everything above was run in a test environment (all containers, the API, the size limits, the headers, backup and restore), but the real certificate and real mail were not.
- The satellite pictures need a provider with a key before real traffic (`.ai/RELEASE_CHECKLIST.md`).
- The files are the same on AWS: an EC2 machine plus the steps above. For photos on S3 and the database on RDS (more safety, more cost) the settings (`STORAGE_TYPE`, `DB_HOST`) exist, but that variant was not built or tried.
