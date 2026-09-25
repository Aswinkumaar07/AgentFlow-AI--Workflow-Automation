import os
import json
import pytest
from app.connectors.security.secret_manager import EnterpriseSecretManager
from app.connectors.models import ConnectorCredentialModel


@pytest.mark.asyncio
async def test_secret_manager_persistence_after_set(tmp_path):
    vault_file = str(tmp_path / 'test_vault.json')
    mgr = EnterpriseSecretManager(vault_path=vault_file)

    cred = ConnectorCredentialModel(
        tenant_id='usr_test_1',
        provider='Google',
        auth_type='OAuth2',
        access_token='secret_real_access_token_12345',
        refresh_token='secret_real_refresh_token_67890',
        token_expires_at=1800000000.0,
        scopes=['gmail.readonly', 'email'],
        account_label='test_user@gmail.com',
    )

    success = await mgr.set_secret('usr_test_1', 'Google', cred)
    assert success is True

    # Confirm vault.json exists
    assert os.path.exists(vault_file)

    # Read raw vault file contents
    with open(vault_file, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # Security check: MUST NOT contain plaintext tokens
    assert 'secret_real_access_token_12345' not in raw_text
    assert 'secret_real_refresh_token_67890' not in raw_text

    # MUST contain encrypted dictionary
    data = json.loads(raw_text)
    assert 'usr_test_1:google' in data
    assert isinstance(data['usr_test_1:google'], str)


@pytest.mark.asyncio
async def test_secret_manager_reload_persistence(tmp_path):
    vault_file = str(tmp_path / 'test_vault.json')

    # Instance 1: write credential
    mgr1 = EnterpriseSecretManager(vault_path=vault_file)
    cred = ConnectorCredentialModel(
        tenant_id='usr_test_2',
        provider='Slack',
        auth_type='OAuth2',
        access_token='slack_access_token_abc',
        refresh_token='slack_refresh_token_def',
        token_expires_at=1900000000.0,
        scopes=['chat:write'],
        account_label='workspace@slack.com',
    )
    await mgr1.set_secret('usr_test_2', 'Slack', cred)

    # Instance 2: fresh manager pointing to same vault file
    mgr2 = EnterpriseSecretManager(vault_path=vault_file)
    retrieved = await mgr2.get_secret('usr_test_2', 'Slack')

    assert retrieved is not None
    assert retrieved.access_token == 'slack_access_token_abc'
    assert retrieved.refresh_token == 'slack_refresh_token_def'
    assert retrieved.token_expires_at == 1900000000.0
    assert retrieved.scopes == ['chat:write']
    assert retrieved.account_label == 'workspace@slack.com'


@pytest.mark.asyncio
async def test_secret_manager_delete_persistence(tmp_path):
    vault_file = str(tmp_path / 'test_vault.json')

    mgr1 = EnterpriseSecretManager(vault_path=vault_file)
    cred = ConnectorCredentialModel(
        tenant_id='usr_test_3',
        provider='GitHub',
        auth_type='OAuth2',
        access_token='github_access_token',
    )
    await mgr1.set_secret('usr_test_3', 'GitHub', cred)

    # Delete credential
    deleted = await mgr1.delete_secret('usr_test_3', 'GitHub')
    assert deleted is True

    # Instance 2: reload and verify credential is absent
    mgr2 = EnterpriseSecretManager(vault_path=vault_file)
    retrieved = await mgr2.get_secret('usr_test_3', 'GitHub')
    assert retrieved is None


@pytest.mark.asyncio
async def test_secret_manager_missing_vault_handling(tmp_path):
    vault_file = str(tmp_path / 'non_existent_vault.json')
    mgr = EnterpriseSecretManager(vault_path=vault_file)

    assert mgr._store == {}
    retrieved = await mgr.get_secret('usr_test_4', 'Google')
    assert retrieved is None


@pytest.mark.asyncio
async def test_secret_manager_corrupt_vault_handling(tmp_path):
    vault_file = str(tmp_path / 'corrupt_vault.json')

    # Write malformed data
    with open(vault_file, 'w', encoding='utf-8') as f:
        f.write('{ INVALID JSON DATA ...')

    # EnterpriseSecretManager should handle corrupt file safely without crashing
    mgr = EnterpriseSecretManager(vault_path=vault_file)
    assert mgr._store == {}
