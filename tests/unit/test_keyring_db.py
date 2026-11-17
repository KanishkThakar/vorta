"""Database keyring selection preserves the system-keyring preference."""

from types import SimpleNamespace

import pytest

from vorta.keyring.abc import VortaKeyring
from vorta.keyring.db import VortaDBKeyring
from vorta.store.models import SettingsModel


@pytest.mark.parametrize('use_system_keyring', [None, True, False])
@pytest.mark.parametrize('system_available', [True, False])
def test_keyring_selection(mocker, use_system_keyring, system_available):
    if use_system_keyring is None:
        SettingsModel.delete().where(SettingsModel.key == 'use_system_keyring').execute()
    else:
        SettingsModel.update(value=use_system_keyring).where(SettingsModel.key == 'use_system_keyring').execute()

    system_keyring = mocker.Mock()
    system_keyring.get_priority.return_value = 5
    system_keyring.__name__ = 'SystemKeyring'
    if not system_available:
        system_keyring.side_effect = RuntimeError('System keyring unavailable')

    mocker.patch.object(VortaKeyring, 'all_keyrings', [('.test', 'DBKeyring'), ('.test', 'SystemKeyring')])
    mocker.patch(
        'vorta.keyring.abc.importlib.import_module',
        return_value=SimpleNamespace(DBKeyring=VortaDBKeyring, SystemKeyring=system_keyring),
    )

    selected = VortaKeyring.get_keyring()

    if system_available and use_system_keyring is not False:
        assert selected is system_keyring.return_value
    else:
        assert isinstance(selected, VortaDBKeyring)
    if use_system_keyring is False:
        system_keyring.assert_not_called()
    if use_system_keyring is None:
        assert not SettingsModel.select().where(SettingsModel.key == 'use_system_keyring').exists()
