"""The web server's size is set from the environment, so a bigger machine only needs a number changed in .env."""
import runpy
from pathlib import Path

import pytest

CONFIG = Path(__file__).resolve().parents[2] / 'gunicorn.conf.py'


def load(monkeypatch, **env):
    for name in ('WEB_WORKERS', 'WEB_THREADS', 'WEB_TIMEOUT'):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    return runpy.run_path(str(CONFIG))


def test_defaults_suit_a_small_server(monkeypatch):
    config = load(monkeypatch)
    assert (config['workers'], config['threads'], config['timeout']) == (3, 4, 30)
    assert config['bind'] == '0.0.0.0:8000'


def test_size_comes_from_the_environment(monkeypatch):
    config = load(monkeypatch, WEB_WORKERS='9', WEB_THREADS='2', WEB_TIMEOUT='45')
    assert (config['workers'], config['threads'], config['timeout']) == (9, 2, 45)


@pytest.mark.parametrize('name', ['WEB_WORKERS', 'WEB_THREADS', 'WEB_TIMEOUT'])
@pytest.mark.parametrize('bad', ['0', '-1', 'many', ''])
def test_a_bad_number_stops_the_start_instead_of_running_with_a_wrong_size(monkeypatch, name, bad):
    with pytest.raises(ValueError, match=name):
        load(monkeypatch, **{name: bad})


def test_the_image_starts_gunicorn_with_this_file():
    dockerfile = (CONFIG.parent / 'Dockerfile').read_text()
    assert '"-c", "gunicorn.conf.py"' in dockerfile
    assert '"--workers"' not in dockerfile  # the number lives in the config file only
