"""Telegram alerts (OWASP A09-4): the right events produce one message, nothing else does."""
import json
import logging
import urllib.error
from unittest import mock

import pytest
from django.core.cache import cache

from common.alerts import AlertHandler, send_alert
from common.tasks import send_telegram_message

@pytest.fixture(autouse=True)
def _clean_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def configured(settings):
    settings.TELEGRAM_BOT_TOKEN = '123:secret-token'
    settings.TELEGRAM_ALERT_CHAT_ID = '-1001'


@pytest.fixture
def queued():
    """The Celery task is replaced, so a test sees what would be sent."""
    with mock.patch('common.tasks.send_telegram_message.delay') as delay:
        yield delay


def _record(message, name='tickbron.security', level=logging.WARNING):
    return logging.LogRecord(name, level, __file__, 1, message, None, None)


@pytest.mark.usefixtures('configured')
class TestSendAlert:
    def test_a_message_is_queued_with_a_prefix(self, queued):
        send_alert('event=lockout user=5 ip=203.0.113.7')

        queued.assert_called_once_with('TICKBRON alert\nevent=lockout user=5 ip=203.0.113.7')

    def test_the_same_message_is_sent_once_per_cooldown(self, queued):
        send_alert('event=lockout user=5 ip=203.0.113.7')
        send_alert('event=lockout user=5 ip=203.0.113.7')
        send_alert('event=lockout user=6 ip=203.0.113.7')

        assert queued.call_count == 2

    def test_a_long_message_is_cut(self, queued):
        send_alert('x' * 5000)

        assert len(queued.call_args.args[0]) < 600


def test_nothing_is_queued_while_alerts_are_not_configured(queued, settings):
    settings.TELEGRAM_BOT_TOKEN = ''
    settings.TELEGRAM_ALERT_CHAT_ID = ''
    send_alert('event=lockout user=5 ip=203.0.113.7')

    queued.assert_not_called()


@pytest.mark.usefixtures('configured')
class TestHandler:
    @pytest.mark.parametrize('event', ['lockout', 'webhook_rejected', 'webhook_not_applied'])
    def test_alert_events_are_sent(self, queued, event):
        AlertHandler().emit(_record(f'event={event} user=none ip=198.51.100.9'))

        queued.assert_called_once()

    @pytest.mark.parametrize('event', ['login_failed', 'permission_denied', 'throttled', 'login_success'])
    def test_everyday_security_events_are_not_sent(self, queued, event):
        AlertHandler().emit(_record(f'event={event} user=none ip=198.51.100.9'))

        queued.assert_not_called()

    def test_an_error_from_any_logger_is_sent(self, queued):
        AlertHandler().emit(_record('Refund 7: unexpected error', name='payments.refunds', level=logging.ERROR))

        queued.assert_called_once()

    def test_a_warning_from_any_logger_is_not_sent(self, queued):
        AlertHandler().emit(_record('Slow request', name='tickbron', level=logging.WARNING))

        queued.assert_not_called()

    def test_a_broken_queue_does_not_break_the_caller(self):
        with mock.patch('common.tasks.send_telegram_message.delay', side_effect=ConnectionError('broker down')):
            with mock.patch.object(AlertHandler, 'handleError') as handle_error:
                AlertHandler().emit(_record('event=lockout user=5 ip=203.0.113.7'))

        handle_error.assert_called_once()


@pytest.mark.usefixtures('configured')
class TestTask:
    def test_it_posts_the_text_to_the_bot_api(self):
        with mock.patch('urllib.request.urlopen') as urlopen:
            send_telegram_message.run('TICKBRON alert\nevent=lockout')

        request = urlopen.call_args.args[0]
        assert request.full_url == 'https://api.telegram.org/bot123:secret-token/sendMessage'
        assert json.loads(request.data) == {'chat_id': '-1001', 'text': 'TICKBRON alert\nevent=lockout'}
        assert urlopen.call_args.kwargs['timeout'] == 5

    def test_a_failure_is_retried_and_the_token_is_never_logged(self, caplog):
        caplog.set_level(logging.DEBUG)
        error = urllib.error.URLError('connection refused')

        with mock.patch('urllib.request.urlopen', side_effect=error):
            with mock.patch.object(send_telegram_message, 'retry', side_effect=RuntimeError('retry')) as retry:
                with pytest.raises(RuntimeError):
                    send_telegram_message.run('text')

        retry.assert_called_once()
        assert 'secret-token' not in caplog.text
        assert 'URLError' in caplog.text


def test_the_alert_handler_is_wired_to_the_security_and_error_loggers():
    from config.logging_config import get_logging_config

    config = get_logging_config()

    for logger_name in ('tickbron.security', 'tickbron', 'django.request'):
        assert 'alerts' in config['loggers'][logger_name]['handlers'], logger_name
    assert 'alerts' in config['root']['handlers']
