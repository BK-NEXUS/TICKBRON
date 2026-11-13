"""Sayt SMS jibermeydi: qollap-quwatlaw komandasınıń juwabı paydalanıwshıǵa tek e-mail arqalı jetedi
(chat/tests/test_notify.py).
Eski SMS xabarlandırıwınan hesh nárse qalmaydı: jiberiwshi, shekler, rozılıq qutısı, kestelar yamasa baǵanalar joq."""
import importlib

import pytest
from django.apps import apps
from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from chat import notify
from users.models import User

pytestmark = pytest.mark.django_db


def test_the_sms_sender_is_gone():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module('common.sms')
    assert not hasattr(notify, 'send_sms')
    assert not hasattr(notify, 'send_reply_sms')


def test_there_are_no_sms_settings():
    assert [name for name in dir(settings) if name.startswith('SMS_')] == []


def test_there_is_no_sms_model_table_or_user_column():
    assert 'SmsDelivery' not in {model.__name__ for model in apps.get_models()}
    assert 'sms_notifications' not in {field.name for field in User._meta.get_fields()}
    with connection.cursor() as cursor:
        tables = connection.introspection.table_names(cursor)
        columns = [column.name for column in connection.introspection.get_table_description(cursor, User._meta.db_table)]
    assert 'chat_sms_deliveries' not in tables
    assert 'sms_notifications' not in columns


class TestRemovalIsReversible(TransactionTestCase):
    """Bir qádem artqa qaytıw SMS kestesin hám rozılıq baǵanasın qaytaradı (bos), alǵa barıw olardı qayta óshiredi."""

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_the_two_migrations_can_be_undone_and_redone(self):
        self._migrate([('chat', '0002_sms_notifications'), ('users', '0012_sms_notifications')])
        with connection.cursor() as cursor:
            assert 'chat_sms_deliveries' in connection.introspection.table_names(cursor)
        self._migrate([('chat', '0003_remove_sms'), ('users', '0013_remove_sms')])
        with connection.cursor() as cursor:
            assert 'chat_sms_deliveries' not in connection.introspection.table_names(cursor)
