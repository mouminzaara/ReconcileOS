"""
State Collection Layer for ReconcileOS.

Provides pluggable collectors to retrieve current identity state from HR
and downstream connected applications into a unified internal representation.
"""

import abc
import uuid
import logging
from django.utils import timezone
from apps.employees.models import Employee
from apps.connectors.models import VPNAccess, GitHubMembership, CloudIAMAccess, SlackAccount
from apps.connectors.adapters import ConnectorRegistry

logger = logging.getLogger(__name__)


class EmployeeNotFoundException(Exception):
    """Raised when an employee cannot be found by ID or email."""
    pass


class InvalidEmployeeIDException(Exception):
    """Raised when an employee ID format is invalid."""
    pass


class BaseConnectorStateCollector(abc.ABC):
    """
    Abstract Base Class for downstream system state collectors.
    
    Connectors (VPN, GitHub, Slack, Cloud IAM) inherit from this interface
    and implement system_name and collect_state(employee).
    """

    @property
    @abc.abstractmethod
    def system_name(self) -> str:
        """
        Returns unique key identifier for the connected system (e.g. 'vpn', 'github', 'cloud', 'slack').
        """
        pass

    @abc.abstractmethod
    def collect_state(self, employee: Employee) -> dict:
        """
        Collects system state for the given employee.
        Returns a dictionary representation of the connector state.
        """
        pass


class VPNStateCollector(BaseConnectorStateCollector):
    """
    State collector for Downstream VPN Connector.
    """

    @property
    def system_name(self) -> str:
        return 'vpn'

    def collect_state(self, employee: Employee) -> dict:
        """
        Retrieves VPN access state for the employee without mutating status.
        """
        try:
            vpn_access = VPNAccess.objects.select_related('employee').get(employee=employee)
            return {
                "connected": True,
                "access_status": vpn_access.status,
                "record_id": str(vpn_access.id),
                "created_at": vpn_access.created_at.isoformat(),
                "updated_at": vpn_access.updated_at.isoformat()
            }
        except VPNAccess.DoesNotExist:
            return {
                "connected": False,
                "access_status": "NOT_PROVISIONED",
                "record_id": None,
                "created_at": None,
                "updated_at": None
            }


class GitHubStateCollector(BaseConnectorStateCollector):
    """
    State collector for Downstream GitHub Connector.
    Translates GitHub API membership status into unified ReconcileOS state representation.
    """

    @property
    def system_name(self) -> str:
        return 'github'

    def collect_state(self, employee: Employee) -> dict:
        """
        Retrieves GitHub organization membership state for the employee.
        """
        try:
            adapter = ConnectorRegistry.get_connector('github')
            info = adapter.get_membership_status(employee)
            return {
                "connected": info.get('connected', True),
                "access_status": info.get('access_status', 'UNKNOWN'),
                "username": info.get('username'),
                "org_name": info.get('org_name')
            }
        except Exception as exc:
            logger.error(f"GitHubStateCollector error for employee '{employee.full_name}': {exc}")
            try:
                membership = GitHubMembership.objects.get(employee=employee)
                return {
                    "connected": True,
                    "access_status": membership.status,
                    "username": membership.github_username,
                    "org_name": membership.org_name
                }
            except GitHubMembership.DoesNotExist:
                return {
                    "connected": False,
                    "access_status": "NOT_PROVISIONED",
                    "username": None,
                    "org_name": None
                }


class CloudStateCollector(BaseConnectorStateCollector):
    """
    State collector for Downstream Cloud IAM Connector.
    """

    @property
    def system_name(self) -> str:
        return 'cloud'

    def collect_state(self, employee: Employee) -> dict:
        """
        Retrieves Cloud IAM role access state for the employee.
        """
        try:
            adapter = ConnectorRegistry.get_connector('cloud')
            cloud_access = adapter.get_cloud_access(employee)
            return {
                "connected": True,
                "access_status": cloud_access.role,
                "role": cloud_access.role,
                "cloud_identity": cloud_access.cloud_identity
            }
        except Exception as exc:
            logger.error(f"CloudStateCollector error for employee '{employee.full_name}': {exc}")
            try:
                access = CloudIAMAccess.objects.get(employee=employee)
                return {
                    "connected": True,
                    "access_status": access.role,
                    "role": access.role,
                    "cloud_identity": access.cloud_identity
                }
            except CloudIAMAccess.DoesNotExist:
                return {
                    "connected": False,
                    "access_status": "NO_ROLE",
                    "role": "NO_ROLE",
                    "cloud_identity": None
                }


class SlackStateCollector(BaseConnectorStateCollector):
    """
    State collector for Downstream Slack Connector.
    """

    @property
    def system_name(self) -> str:
        return 'slack'

    def collect_state(self, employee: Employee) -> dict:
        """
        Retrieves Slack account status for the employee.
        """
        try:
            adapter = ConnectorRegistry.get_connector('slack')
            slack_account = adapter.get_slack_account(employee)
            return {
                "connected": True,
                "access_status": slack_account.status,
                "slack_user_id": slack_account.slack_user_id
            }
        except Exception as exc:
            logger.error(f"SlackStateCollector error for employee '{employee.full_name}': {exc}")
            try:
                account = SlackAccount.objects.get(employee=employee)
                return {
                    "connected": True,
                    "access_status": account.status,
                    "slack_user_id": account.slack_user_id
                }
            except SlackAccount.DoesNotExist:
                return {
                    "connected": False,
                    "access_status": "DEACTIVATED",
                    "slack_user_id": None
                }


class StateCollector:
    """
    Unified Multi-System State Aggregator.
    
    Collects HR system of record identity status along with downstream system states
    from registered connector collectors.
    """

    def __init__(self, connector_collectors=None):
        """
        Initializes StateCollector with a list of system collectors.
        Defaults to [VPNStateCollector(), GitHubStateCollector(), CloudStateCollector(), SlackStateCollector()].
        """
        if connector_collectors is None:
            self.connector_collectors = [
                VPNStateCollector(),
                GitHubStateCollector(),
                CloudStateCollector(),
                SlackStateCollector()
            ]
        else:
            self.connector_collectors = connector_collectors

    def _resolve_employee(self, employee_id_or_email) -> Employee:
        """
        Validates input and resolves to an Employee instance.
        """
        if isinstance(employee_id_or_email, Employee):
            return employee_id_or_email

        val = str(employee_id_or_email).strip()

        # Try lookup by UUID
        try:
            emp_uuid = uuid.UUID(val)
            try:
                return Employee.objects.get(pk=emp_uuid)
            except Employee.DoesNotExist:
                raise EmployeeNotFoundException(f"Employee with UUID '{val}' does not exist.")
        except (ValueError, AttributeError, TypeError):
            # Not a valid UUID, try lookup by email
            if '@' in val:
                try:
                    return Employee.objects.get(email__iexact=val)
                except Employee.DoesNotExist:
                    raise EmployeeNotFoundException(f"Employee with email '{val}' does not exist.")
            raise InvalidEmployeeIDException(f"Invalid employee identifier format: '{val}'. Must be UUID or valid email.")

    def collect_employee_state(self, employee_id_or_email) -> dict:
        """
        Collects unified multi-system state for a single employee.
        Returns a dictionary internal representation payload.
        """
        employee = self._resolve_employee(employee_id_or_email)
        collected_timestamp = timezone.now().isoformat()

        systems_state = {}
        for collector in self.connector_collectors:
            systems_state[collector.system_name] = collector.collect_state(employee)

        return {
            "employee_id": str(employee.id),
            "employee_name": employee.full_name,
            "employee_email": employee.email,
            "department": employee.department,
            "employee_status": employee.status,
            "collected_at": collected_timestamp,
            "systems": systems_state
        }

    def collect_all_states(self) -> list:
        """
        Collects unified multi-system states for all employees in HR system.
        """
        employees = Employee.objects.all().order_by('full_name')
        return [self.collect_employee_state(emp) for emp in employees]
