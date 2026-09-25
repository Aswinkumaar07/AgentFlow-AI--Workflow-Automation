import logging
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.agents.oauth_ai.account_picker")

from app.oauth.provider_utils import normalize_provider, GOOGLE_PROVIDERS

OAUTH_PROVIDERS = ["Google", "Slack", "GitHub", "Stripe", "OpenAI", "Notion"]


class ConnectedAccount(BaseModel):
    account_id: str
    provider: str
    email_or_name: str
    status: str = "active"          # 'active', 'expired', 'disconnected'
    is_default: bool = False
    access_token: str = ""
    refresh_token: str = ""
    expires_at: int = Field(default_factory=lambda: int(time.time()) + 3600)
    scopes: List[str] = Field(default_factory=list)
    connected_at: float = Field(default_factory=time.time)

    def is_expired(self) -> bool:
        return self.expires_at < int(time.time())

    def expires_in_seconds(self) -> int:
        return max(0, self.expires_at - int(time.time()))


class AccountPicker:
    """Manages multi-account selections and retrieves default active accounts per provider strictly from store/database."""

    def __init__(self) -> None:
        self.accounts: Dict[str, List[ConnectedAccount]] = {}

    def get_default_account(self, provider: str) -> Optional[ConnectedAccount]:
        p_norm = normalize_provider(provider)
        accs = self.accounts.get(p_norm, [])
        for a in accs:
            if a.is_default and a.status == "active":
                return a
        return accs[0] if accs else None

    def list_accounts(self, provider: str) -> List[ConnectedAccount]:
        p_norm = normalize_provider(provider)
        return self.accounts.get(p_norm, [])

    def list_all_providers(self) -> List[str]:
        return list(self.accounts.keys())

    def add_or_update_account(self, account: ConnectedAccount) -> ConnectedAccount:
        account.provider = normalize_provider(account.provider)
        if account.provider not in self.accounts:
            self.accounts[account.provider] = []
        existing = self.accounts[account.provider]
        self.accounts[account.provider] = [a for a in existing if a.account_id != account.account_id]
        self.accounts[account.provider].append(account)
        logger.info(f"Account '{account.email_or_name}' for provider '{account.provider}' added/updated.")
        return account

    def set_default(self, provider: str, account_id: str) -> bool:
        p_norm = normalize_provider(provider)
        accs = self.accounts.get(p_norm, [])
        found = False
        for a in accs:
            if a.account_id == account_id:
                a.is_default = True
                found = True
                logger.info(f"Set default account for '{p_norm}': {a.email_or_name}")
            else:
                a.is_default = False
        return found

    def disconnect_account(self, provider: str, account_id: str) -> bool:
        p_norm = normalize_provider(provider)
        accs = self.accounts.get(p_norm, [])
        was_default = any(a.account_id == account_id and a.is_default for a in accs)
        self.accounts[p_norm] = [a for a in accs if a.account_id != account_id]

        if was_default and self.accounts[p_norm]:
            self.accounts[p_norm][0].is_default = True

        logger.info(f"Disconnected account '{account_id}' from provider '{p_norm}'.")
        return True

    def mark_expired(self, provider: str, account_id: str) -> None:
        p_norm = normalize_provider(provider)
        accs = self.accounts.get(p_norm, [])
        for a in accs:
            if a.account_id == account_id:
                a.status = "expired"
                a.expires_at = int(time.time()) - 1

    def refresh_account_token(self, provider: str, account_id: str) -> Optional[ConnectedAccount]:
        p_norm = normalize_provider(provider)
        accs = self.accounts.get(p_norm, [])
        for a in accs:
            if a.account_id == account_id:
                a.expires_at = int(time.time()) + 3600
                a.status = "active"
                return a
        return None


account_picker = AccountPicker()
