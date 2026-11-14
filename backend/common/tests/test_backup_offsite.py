"""Túngi backup sonday-aq serverden sırtqı jerge de baradı (restic penen shifrlanǵan, reje .ai/PLAN_INFRA_SCALE.md, A1
bólegi).

Ol deploy/offsite.env penen qosıladı. Skript jalǵan `docker`, jalǵan `restic` hám jalǵan `curl` ǵa qarsı isleydi,
olar ne soralǵanın log faylǵa jazadı.
"""
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

from common.tests.test_backup_script import FAKE_DOCKER, REPO, backups

FAKE_RESTIC = """#!/bin/sh
echo "restic $*" >> "$FAKE_LOG"
[ -n "$FAKE_RESTIC_FAIL" ] && { echo "restic: unable to open the repository" >&2; exit 1; }
exit 0
"""
# curl ge sazlamaları standart kirisiw arqalı beriledi (token process dizimde kórinbewi kerek), sol sebepli jalǵan eki jaqtı da
# jazadı
FAKE_CURL = """#!/bin/sh
echo "curl $*" >> "$FAKE_LOG"
cat >> "$FAKE_LOG"
"""
OFFSITE = """RESTIC_REPOSITORY=s3:s3.eu-west-1.amazonaws.com/tickbron-backups-test
RESTIC_PASSWORD=very-secret-repository-password
AWS_ACCESS_KEY_ID=AKIAFAKEFAKEFAKE
AWS_SECRET_ACCESS_KEY=very-secret-access-key
"""
TELEGRAM = """TELEGRAM_BOT_TOKEN=123456:secret-bot-token
TELEGRAM_ALERT_CHAT_ID=-100777
"""


def executable(path, text):
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


@pytest.fixture
def server(tmp_path):
    (tmp_path / 'deploy').mkdir()
    shutil.copy(REPO / 'deploy' / 'backup.sh', tmp_path / 'deploy' / 'backup.sh')
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    executable(bin_dir / 'docker', FAKE_DOCKER)
    executable(bin_dir / 'restic', FAKE_RESTIC)
    executable(bin_dir / 'curl', FAKE_CURL)
    return tmp_path


def configure(server, text):
    (server / 'deploy' / 'offsite.env').write_text(text)
    (server / 'deploy' / 'offsite.env').chmod(0o600)


def run(server, **env):
    environment = {**os.environ, 'PATH': f'{server / "bin"}:{os.environ["PATH"]}', 'FAKE_LOG': str(server / 'log.txt'), **env}
    return subprocess.run(['sh', str(server / 'deploy' / 'backup.sh')], capture_output=True, text=True, env=environment)


def log(server):
    path = server / 'log.txt'
    return path.read_text() if path.exists() else ''


def test_without_the_offsite_file_nothing_is_sent_anywhere(server):
    result = run(server)

    assert result.returncode == 0, result.stderr
    assert 'restic' not in log(server)
    assert 'Offsite' not in result.stdout


def test_with_the_offsite_file_both_files_are_sent_then_old_copies_are_removed(server):
    configure(server, OFFSITE)

    result = run(server)

    assert result.returncode == 0, result.stderr
    lines = log(server).splitlines()
    assert lines[0].startswith('restic backup ') and '.dump' in lines[0] and '.tar.gz' in lines[0]
    assert lines[1] == 'restic forget --keep-daily 14 --keep-weekly 8 --keep-monthly 6 --prune'
    assert 'Offsite copy done' in result.stdout


def test_the_retention_can_be_changed_in_the_offsite_file(server):
    configure(server, OFFSITE + 'KEEP_DAILY=30\nKEEP_WEEKLY=4\nKEEP_MONTHLY=12\n')

    run(server)

    assert 'restic forget --keep-daily 30 --keep-weekly 4 --keep-monthly 12 --prune' in log(server)


def test_a_failed_upload_fails_the_run_but_keeps_the_local_backup(server):
    configure(server, OFFSITE)

    result = run(server, FAKE_RESTIC_FAIL='1')

    assert result.returncode != 0
    assert 'Offsite copy done' not in result.stdout
    assert 'offsite' in result.stderr.lower()
    assert len(backups(server)) == 2
    assert 'restic forget' not in log(server)


def test_a_failed_run_tells_the_team_on_telegram_without_showing_the_token(server):
    configure(server, OFFSITE + TELEGRAM)

    result = run(server, FAKE_DB_FAIL='1')

    assert result.returncode != 0
    entries = log(server)
    assert 'api.telegram.org/bot123456:secret-bot-token/sendMessage' in entries
    assert '-100777' in entries and 'backup failed' in entries.lower()
    assert 'secret-bot-token' not in next(line for line in entries.splitlines() if line.startswith('curl '))


def test_a_good_run_sends_no_alert(server):
    configure(server, OFFSITE + TELEGRAM)

    assert run(server).returncode == 0
    assert 'curl' not in log(server)


def test_without_telegram_settings_a_failed_run_still_fails_cleanly(server):
    configure(server, OFFSITE)

    result = run(server, FAKE_DB_FAIL='1')

    assert result.returncode != 0
    assert 'curl' not in log(server)


def test_the_passwords_and_keys_are_never_printed(server):
    configure(server, OFFSITE + TELEGRAM)

    for failure in ({}, {'FAKE_RESTIC_FAIL': '1'}, {'FAKE_DB_FAIL': '1'}):
        result = run(server, **failure)
        shown = result.stdout + result.stderr
        for secret in ('very-secret-repository-password', 'very-secret-access-key', 'AKIAFAKEFAKEFAKE', 'secret-bot-token'):
            assert secret not in shown


def test_a_settings_file_that_others_can_read_is_refused_and_never_run(server):
    # offsite.env shell retinde isletiledi: basqa paydalanıwshı jaza alsa, ol serverde komanda isletedi
    configure(server, OFFSITE + 'touch "$PWD/pwned"' + chr(10))
    (server / 'deploy' / 'offsite.env').chmod(0o666)

    result = run(server)

    assert result.returncode != 0
    assert 'chmod 600' in result.stderr
    assert not (server / 'pwned').exists()
    assert 'restic' not in log(server)
