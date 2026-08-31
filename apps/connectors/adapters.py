"""
Connector Abstraction Layer for ReconcileOS.

Provides pluggable, system-agnostic connector adapters to execute repair actions
against downstream target systems (VPN, GitHub, Slack, Cloud IAM).
"""

import abc
import os
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Type
from apps.employees.models import Employee
from .models import (
    VPNAccess, VPNAccessStatus,
    GitHubMembership, GitHubAccessStatus,
    CloudIAMAccess, CloudRole,
    SlackAccount, SlackAccountStatus
)

logger = logging.getLogger(__name__)


class ConnectorException(Exception):
    """Base exception for connector operations."""
    pass


class UnsupportedConnectorException(ConnectorException):
    """Raised when a connector is requested for an unregistered system."""
    pass


class ActionNotSupportedException(ConnectorException):
    """Raised when an action is not supported by the specified connector."""
    pass


class BaseConnectorAdapter(abc.ABC):
    """
    Abstract Base Class for downstream target system connectors.

    Every connector implementation (VPN, GitHub, Cloud IAM, Slack) inherits from this interface
    and implements system_name and execute_action().
    """

    @property
    @abc.abstractmethod
    def system_name(self) -> str:
        """
        Unique system identifier key (e.g. 'vpn', 'github', 'cloud', 'slack').
        """
        pass

    @abc.abstractmethod
    def execute_action(self, employee: Employee, action: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executes a standardized repair action for an employee against the downstream system.

        Returns:
            Dict containing:
            - 'success': bool
            - 'message': str
            - 'details': dict
        """
        pass


class VPNConnectorAdapter(BaseConnectorAdapter):
    """
    Simulated Downstream VPN Connector Adapter.
    Executes access provisioning and revocation operations via VPNAccess model methods.
    Supports development/testing failure modes to simulate external API timeouts.
    """

    def __init__(self):
        self.fail_next_n_attempts: int = 0
        self.fail_with_state_applied: bool = False

    def set_simulated_failure(self, fail_next_n: int = 1, apply_state_first: bool = False):
        """
        Enables testing failure mode for the next N execution attempts.
        """
        self.fail_next_n_attempts = fail_next_n
        self.fail_with_state_applied = apply_state_first
        logger.warning(
            f"VPNConnectorAdapter failure mode set for next {fail_next_n} attempt(s) "
            f"(apply_state_first={apply_state_first})."
        )

    @property
    def system_name(self) -> str:
        return 'vpn'

    def execute_action(self, employee: Employee, action: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executes VPN access control actions idempotently (e.g. DISABLE VPN ACCESS or ENABLE VPN ACCESS).
        """
        action_upper = (action or '').strip().upper()
        logger.info(f"VPNConnectorAdapter executing action '{action_upper}' for employee '{employee.full_name}'.")

        vpn_access, _ = VPNAccess.objects.get_or_create(
            employee=employee,
            defaults={'status': VPNAccessStatus.DISABLED}
        )

        if self.fail_next_n_attempts > 0:
            self.fail_next_n_attempts -= 1

            if self.fail_with_state_applied:
                if 'DISABLE' in action_upper:
                    vpn_access.disable()
                elif 'ENABLE' in action_upper:
                    vpn_access.enable()

                logger.warning(
                    f"VPNConnectorAdapter simulating API timeout AFTER downstream state update for '{employee.full_name}'."
                )
                return {
                    "success": False,
                    "message": f"Simulated external VPN API gateway timeout AFTER state update for {employee.full_name} (HTTP 504)",
                    "details": {
                        "error_code": 504,
                        "transient": True,
                        "simulated": True,
                        "state_applied": True
                    }
                }
            else:
                logger.warning(
                    f"VPNConnectorAdapter simulating transient external API failure for '{employee.full_name}'."
                )
                return {
                    "success": False,
                    "message": f"Simulated external VPN API failure for {employee.full_name}: Gateway Connection Timeout (HTTP 503)",
                    "details": {
                        "error_code": 503,
                        "transient": True,
                        "simulated": True,
                        "state_applied": False
                    }
                }

        if 'DISABLE' in action_upper or action_upper == 'DISABLE VPN ACCESS':
            status_changed = vpn_access.disable()
            return {
                "success": True,
                "message": (
                    f"Successfully disabled VPN access for {employee.full_name}."
                    if status_changed else
                    f"VPN access for {employee.full_name} was already disabled."
                ),
                "details": {
                    "action": "DISABLE",
                    "status_changed": status_changed,
                    "already_satisfied": not status_changed,
                    "current_status": vpn_access.status,
                    "vpn_access_id": str(vpn_access.id)
                }
            }
        elif 'ENABLE' in action_upper or action_upper == 'ENABLE VPN ACCESS':
            status_changed = vpn_access.enable()
            return {
                "success": True,
                "message": (
                    f"Successfully enabled VPN access for {employee.full_name}."
                    if status_changed else
                    f"VPN access for {employee.full_name} was already enabled."
                ),
                "details": {
                    "action": "ENABLE",
                    "status_changed": status_changed,
                    "already_satisfied": not status_changed,
                    "current_status": vpn_access.status,
                    "vpn_access_id": str(vpn_access.id)
                }
            }
        else:
            raise ActionNotSupportedException(
                f"VPN Connector does not support action '{action}'. Supported actions: DISABLE VPN ACCESS, ENABLE VPN ACCESS."
            )


class GitHubConnectorAdapter(BaseConnectorAdapter):
    """
    GitHub Downstream Target System Connector Adapter.
    """

    def __init__(self):
        self.org_name = os.environ.get('GITHUB_ORG_NAME', 'reconcileos-org')
        self.token = os.environ.get('GITHUB_ACCESS_TOKEN', os.environ.get('GITHUB_TOKEN', ''))
        self.base_url = os.environ.get('GITHUB_API_BASE_URL', 'https://api.github.com').rstrip('/')

    @property
    def system_name(self) -> str:
        return 'github'

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ReconcileOS-IntegrityEngine"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _resolve_username(self, employee: Employee) -> str:
        default_username = employee.email.split('@')[0].lower().replace('.', '_') + '_gh'
        membership, _ = GitHubMembership.objects.get_or_create(
            employee=employee,
            defaults={
                'github_username': default_username,
                'org_name': self.org_name,
                'status': GitHubAccessStatus.MEMBER
            }
        )
        return membership.github_username

    def get_membership_status(self, employee: Employee) -> Dict[str, Any]:
        username = self._resolve_username(employee)

        if self.token:
            url = f"{self.base_url}/orgs/{self.org_name}/members/{username}"
            logger.info(f"GitHubConnectorAdapter querying GET {url}...")
            req = urllib.request.Request(url, headers=self._get_headers(), method='GET')
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status in [204, 200]:
                        status_val = GitHubAccessStatus.MEMBER
                    else:
                        status_val = GitHubAccessStatus.REVOKED
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    status_val = GitHubAccessStatus.REVOKED
                elif exc.code in [401, 403]:
                    raise ConnectorException(
                        f"GitHub API Authentication / Authorization failure: HTTP {exc.code} - {exc.reason}"
                    )
                else:
                    raise ConnectorException(
                        f"GitHub API Error querying membership for '{username}': HTTP {exc.code} - {exc.reason}"
                    )
            except urllib.error.URLError as exc:
                logger.error(f"GitHub API Connection failure for '{username}': {exc.reason}")
                raise ConnectorException(f"GitHub API connection failure: {exc.reason}") from exc

            membership = GitHubMembership.objects.filter(employee=employee).first()
            if membership and membership.status != status_val:
                membership.status = status_val
                membership.save(update_fields=['status', 'updated_at'])

            return {
                "connected": True,
                "access_status": status_val,
                "username": username,
                "org_name": self.org_name
            }

        membership = GitHubMembership.objects.filter(employee=employee).first()
        status_val = membership.status if membership else GitHubAccessStatus.REVOKED
        return {
            "connected": True,
            "access_status": status_val,
            "username": username,
            "org_name": self.org_name
        }

    def execute_action(self, employee: Employee, action: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        action_upper = (action or '').strip().upper()
        logger.info(f"GitHubConnectorAdapter executing action '{action_upper}' for employee '{employee.full_name}'.")

        username = self._resolve_username(employee)

        if not any(k in action_upper for k in ['REVOKE', 'REMOVE', 'DISABLE']):
            raise ActionNotSupportedException(
                f"GitHub Connector does not support action '{action}'. "
                f"Supported actions: REMOVE GITHUB ACCESS, SET GITHUB ACCESS TO REVOKED."
            )

        current_info = self.get_membership_status(employee)
        current_status = current_info.get('access_status')

        if current_status in [GitHubAccessStatus.REVOKED, GitHubAccessStatus.NOT_MEMBER]:
            return {
                "success": True,
                "message": f"GitHub organization access for {employee.full_name} ({username}) is already revoked.",
                "details": {
                    "action": "REVOKE",
                    "status_changed": False,
                    "already_satisfied": True,
                    "access_status": GitHubAccessStatus.REVOKED,
                    "username": username,
                    "org_name": self.org_name
                }
            }

        if self.token:
            url = f"{self.base_url}/orgs/{self.org_name}/members/{username}"
            req = urllib.request.Request(url, headers=self._get_headers(), method='DELETE')
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status in [204, 200]:
                        membership = GitHubMembership.objects.filter(employee=employee).first()
                        if membership:
                            membership.revoke()
                        return {
                            "success": True,
                            "message": f"Successfully removed GitHub organization access for {employee.full_name} ({username}).",
                            "details": {
                                "action": "REVOKE",
                                "status_changed": True,
                                "already_satisfied": False,
                                "access_status": GitHubAccessStatus.REVOKED,
                                "username": username,
                                "org_name": self.org_name
                            }
                        }
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    membership = GitHubMembership.objects.filter(employee=employee).first()
                    if membership:
                        membership.revoke()
                    return {
                        "success": True,
                        "message": f"GitHub organization access for {employee.full_name} ({username}) was already revoked.",
                        "details": {
                            "action": "REVOKE",
                            "status_changed": False,
                            "already_satisfied": True,
                            "access_status": GitHubAccessStatus.REVOKED,
                            "username": username,
                            "org_name": self.org_name
                        }
                    }
                elif exc.code in [401, 403]:
                    raise ConnectorException(
                        f"GitHub API Authentication / Authorization failure: HTTP {exc.code} - {exc.reason}"
                    )
                else:
                    raise ConnectorException(
                        f"GitHub API error revoking membership for '{username}': HTTP {exc.code} - {exc.reason}"
                    )
            except urllib.error.URLError as exc:
                raise ConnectorException(f"GitHub API connection failure during revoke: {exc.reason}") from exc

        membership = GitHubMembership.objects.filter(employee=employee).first()
        status_changed = False
        if membership:
            status_changed = membership.revoke()

        return {
            "success": True,
            "message": (
                f"Successfully removed GitHub organization access for {employee.full_name} ({username})."
                if status_changed else
                f"GitHub organization access for {employee.full_name} ({username}) was already revoked."
            ),
            "details": {
                "action": "REVOKE",
                "status_changed": status_changed,
                "already_satisfied": not status_changed,
                "access_status": GitHubAccessStatus.REVOKED,
                "username": username,
                "org_name": self.org_name
            }
        }


class CloudConnectorAdapter(BaseConnectorAdapter):
    """
    Simulated Downstream Cloud IAM Connector Adapter.
    Manages Cloud IAM role assignments (e.g. DEVELOPER_ROLE, ADMIN_ROLE, NO_ROLE) for employees.
    """

    @property
    def system_name(self) -> str:
        return 'cloud'

    def get_cloud_access(self, employee: Employee) -> CloudIAMAccess:
        cloud_arn = f"arn:aws:iam::123456789012:user/{employee.email.split('@')[0]}"
        access, _ = CloudIAMAccess.objects.get_or_create(
            employee=employee,
            defaults={'cloud_identity': cloud_arn, 'role': CloudRole.NO_ROLE}
        )
        return access

    def execute_action(self, employee: Employee, action: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executes Cloud IAM role revocation (e.g. REVOKE CLOUD PERMISSIONS or REMOVE CLOUD ROLE).
        """
        action_upper = (action or '').strip().upper()
        logger.info(f"CloudConnectorAdapter executing action '{action_upper}' for employee '{employee.full_name}'.")

        cloud_access = self.get_cloud_access(employee)

        if not any(k in action_upper for k in ['REVOKE', 'REMOVE', 'DISABLE', 'NO_ROLE']):
            raise ActionNotSupportedException(
                f"Cloud Connector does not support action '{action}'. "
                f"Supported actions: REVOKE CLOUD PERMISSIONS, REMOVE CLOUD ROLE, SET CLOUD ROLE TO NO_ROLE."
            )

        status_changed = cloud_access.revoke()
        return {
            "success": True,
            "message": (
                f"Successfully revoked Cloud IAM role permissions for {employee.full_name}."
                if status_changed else
                f"Cloud IAM permissions for {employee.full_name} were already revoked."
            ),
            "details": {
                "action": "REVOKE",
                "status_changed": status_changed,
                "already_satisfied": not status_changed,
                "role": cloud_access.role,
                "cloud_identity": cloud_access.cloud_identity
            }
        }


class SlackConnectorAdapter(BaseConnectorAdapter):
    """
    Simulated Downstream Slack Workspace Connector Adapter.
    Manages Slack enterprise account status (ACTIVE or DEACTIVATED) for employees.
    """

    @property
    def system_name(self) -> str:
        return 'slack'

    def get_slack_account(self, employee: Employee) -> SlackAccount:
        slack_id = f"U{abs(hash(employee.email)) % 100000000:08d}"
        account, _ = SlackAccount.objects.get_or_create(
            employee=employee,
            defaults={'slack_user_id': slack_id, 'status': SlackAccountStatus.DEACTIVATED}
        )
        return account

    def execute_action(self, employee: Employee, action: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executes Slack workspace account deactivation (e.g. DISABLE SLACK ACCOUNT or DEACTIVATE SLACK ACCOUNT).
        """
        action_upper = (action or '').strip().upper()
        logger.info(f"SlackConnectorAdapter executing action '{action_upper}' for employee '{employee.full_name}'.")

        slack_account = self.get_slack_account(employee)

        if not any(k in action_upper for k in ['DISABLE', 'DEACTIVATE', 'REVOKE']):
            raise ActionNotSupportedException(
                f"Slack Connector does not support action '{action}'. "
                f"Supported actions: DISABLE SLACK ACCOUNT, DEACTIVATE SLACK ACCOUNT."
            )

        status_changed = slack_account.deactivate()
        return {
            "success": True,
            "message": (
                f"Successfully deactivated Slack workspace account for {employee.full_name}."
                if status_changed else
                f"Slack account for {employee.full_name} was already deactivated."
            ),
            "details": {
                "action": "DEACTIVATE",
                "status_changed": status_changed,
                "already_satisfied": not status_changed,
                "current_status": slack_account.status,
                "slack_user_id": slack_account.slack_user_id
            }
        }


class ConnectorRegistry:
    """
    Centralized Registry for Downstream Connector Adapters.
    """
    _registry: Dict[str, BaseConnectorAdapter] = {}

    @classmethod
    def register(cls, adapter: BaseConnectorAdapter):
        """Registers a connector adapter instance."""
        sys_key = adapter.system_name.strip().lower()
        cls._registry[sys_key] = adapter
        logger.info(f"Registered connector adapter for system '{sys_key}'.")

    @classmethod
    def get_connector(cls, system_name: str) -> BaseConnectorAdapter:
        """
        Retrieves registered connector adapter by system name (case-insensitive).
        Raises UnsupportedConnectorException if not found.
        """
        if not system_name:
            raise UnsupportedConnectorException("Target system name cannot be empty.")

        sys_key = str(system_name).strip().lower()

        # Lazy auto-register default connectors if empty
        if not cls._registry:
            cls.register(VPNConnectorAdapter())
            cls.register(GitHubConnectorAdapter())
            cls.register(CloudConnectorAdapter())
            cls.register(SlackConnectorAdapter())

        if sys_key in cls._registry:
            return cls._registry[sys_key]

        raise UnsupportedConnectorException(
            f"No registered connector adapter for system '{system_name}'. "
            f"Supported systems: {list(cls._registry.keys())}."
        )


# Register default built-in connectors
ConnectorRegistry.register(VPNConnectorAdapter())
ConnectorRegistry.register(GitHubConnectorAdapter())
ConnectorRegistry.register(CloudConnectorAdapter())
ConnectorRegistry.register(SlackConnectorAdapter())
