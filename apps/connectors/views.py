"""
API Views and ViewSets for Simulated VPN Connector.
"""

import uuid
from django.http import Http404
from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.accounts.permissions import IsAdminUserRole, IsViewerUserRole
from apps.employees.models import Employee
from .models import VPNAccess, VPNAccessStatus
from .serializers import VPNAccessSerializer


class VPNAccessViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing Simulated VPN Access states.
    
    Standard Endpoints:
    - GET    /api/v1/vpn/                       -> List all VPN access records (filterable, searchable)
    - POST   /api/v1/vpn/                       -> Create explicit VPN access record
    - GET    /api/v1/vpn/<employee_id>/         -> Retrieve VPN access state (auto-initializes to DISABLED if absent)
    - PUT    /api/v1/vpn/<employee_id>/         -> Update VPN access record
    - PATCH  /api/v1/vpn/<employee_id>/         -> Partial update VPN access record
    - DELETE /api/v1/vpn/<employee_id>/         -> Remove VPN access record
    
    Action Endpoints:
    - POST   /api/v1/vpn/<employee_id>/enable/  -> Explicitly enable VPN access for employee
    - POST   /api/v1/vpn/<employee_id>/disable/ -> Explicitly disable VPN access for employee
    """
    queryset = VPNAccess.objects.select_related('employee').all()
    serializer_class = VPNAccessSerializer
    lookup_field = 'employee_id'
    lookup_url_kwarg = 'employee_id'

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'employee__department', 'employee__status']
    search_fields = ['employee__full_name', 'employee__email', 'employee__department']
    ordering_fields = ['created_at', 'updated_at', 'status', 'employee__full_name']
    ordering = ['-updated_at']

    def get_permissions(self):
        """
        Enforce ReconcileOS RBAC least-privilege policy:
        - Mutations (create, update, partial_update, destroy, enable, disable) and
          any non-safe HTTP methods require ADMIN role.
        - Read actions (list, retrieve, HEAD, OPTIONS) require authenticated user (VIEWER, OPERATOR, ADMIN).
        - Unauthenticated requests are rejected with HTTP 401.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'enable', 'disable'] or self.request.method not in permissions.SAFE_METHODS:
            return [IsAdminUserRole()]
        return [IsViewerUserRole()]

    def get_employee_or_404(self, employee_id):
        """
        Validates employee_id format and retrieves the Employee instance.
        Raises Http404 if invalid UUID or if employee does not exist.
        """
        try:
            val = uuid.UUID(str(employee_id))
        except (ValueError, AttributeError, TypeError):
            raise Http404(f"Invalid employee ID format: '{employee_id}'. Must be a valid UUID.")

        try:
            return Employee.objects.get(pk=val)
        except Employee.DoesNotExist:
            raise Http404(f"Employee with ID '{employee_id}' does not exist.")

    def get_object(self):
        """
        Retrieves the VPNAccess record corresponding to the employee_id in URL.
        
        Auto-Initialization Behavior:
        If the employee exists in the HR system but does not yet possess a VPN
        access record, this method automatically creates a new record with status
        set to DISABLED (defaulting to least-privilege zero-trust state).
        """
        employee_id = self.kwargs.get(self.lookup_url_kwarg)
        employee = self.get_employee_or_404(employee_id)

        vpn_access, _ = VPNAccess.objects.get_or_create(
            employee=employee,
            defaults={'status': VPNAccessStatus.DISABLED}
        )
        return vpn_access

    @action(detail=True, methods=['post'], url_path='enable')
    def enable(self, request, employee_id=None):
        """
        Explicit action endpoint to enable VPN access for an employee.
        Auto-initializes the record to DISABLED first if absent, then sets to ENABLED.
        """
        vpn_access = self.get_object()
        status_changed = vpn_access.enable()

        response_data = {
            "status": "success",
            "message": "VPN access enabled successfully." if status_changed else "VPN access is already enabled.",
            "status_changed": status_changed,
            "action": "ENABLE",
            "vpn_access": VPNAccessSerializer(vpn_access).data
        }
        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='disable')
    def disable(self, request, employee_id=None):
        """
        Explicit action endpoint to disable VPN access for an employee.
        Auto-initializes the record to DISABLED first if absent, then sets to DISABLED.
        """
        vpn_access = self.get_object()
        status_changed = vpn_access.disable()

        response_data = {
            "status": "success",
            "message": "VPN access disabled successfully." if status_changed else "VPN access is already disabled.",
            "status_changed": status_changed,
            "action": "DISABLE",
            "vpn_access": VPNAccessSerializer(vpn_access).data
        }
        return Response(response_data, status=status.HTTP_200_OK)


import time
import urllib.request
import urllib.error
from rest_framework.views import APIView
from .models import GitHubMembership, CloudIAMAccess, SlackAccount
from .adapters import ConnectorRegistry


class ConnectorHealthCheckView(APIView):
    """
    Truthful Health Check API endpoint for connected target system adapters.

    Verifies the actual runtime capabilities and state of each connector without
    mutating database state or executing repair operations.
    Clearly distinguishes local simulations, database fallbacks, and live external APIs.
    """
    permission_classes = [IsViewerUserRole]

    def _check_system(self, system_key: str, request=None) -> dict:
        key = system_key.lower().strip()
        start = time.perf_counter()

        simulate_timeout = request and request.query_params.get('simulate_timeout') in ['1', 'true', 'True']
        simulate_error = request and request.query_params.get('simulate_error') in ['1', 'true', 'True']

        if simulate_timeout:
            return {
                "key": key,
                "name": key.upper(),
                "status": "TIMEOUT",
                "reachability": "Timeout (Simulated)",
                "latency_ms": 5000.0,
                "is_simulated": True,
                "is_live_external": False,
                "message": f"Connection check to '{key}' timed out after 5000ms."
            }

        if simulate_error:
            return {
                "key": key,
                "name": key.upper(),
                "status": "ERROR",
                "reachability": "Simulated Error",
                "latency_ms": 12.0,
                "is_simulated": True,
                "is_live_external": False,
                "message": f"Simulated connection failure encountered for '{key}'."
            }

        if key == 'hr':
            try:
                count = Employee.objects.count()
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                return {
                    "key": "hr",
                    "name": "HR Directory (System of Record)",
                    "mode": "Database fallback",
                    "is_simulated": False,
                    "is_live_external": False,
                    "status": "HEALTHY",
                    "reachability": "Local Database Reachable",
                    "latency_ms": duration_ms,
                    "message": f"Primary HR system of record verified. {count} employee record(s) indexed in database."
                }
            except Exception as exc:
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                return {
                    "key": "hr",
                    "name": "HR Directory (System of Record)",
                    "mode": "Database fallback",
                    "is_simulated": False,
                    "is_live_external": False,
                    "status": "ERROR",
                    "reachability": "Database Error",
                    "latency_ms": duration_ms,
                    "message": f"HR database query failed: {exc}"
                }

        elif key == 'vpn':
            try:
                adapter = ConnectorRegistry.get_connector('vpn')
                if getattr(adapter, 'fail_next_n_attempts', 0) > 0:
                    duration_ms = round((time.perf_counter() - start) * 1000, 2)
                    return {
                        "key": "vpn",
                        "name": "Enterprise VPN Gateway",
                        "mode": "Local simulation",
                        "is_simulated": True,
                        "is_live_external": False,
                        "status": "SIMULATED_FAILURE",
                        "reachability": "Simulated Gateway Failure",
                        "latency_ms": duration_ms,
                        "message": "Simulated VPN API gateway failure hook is currently active for testing."
                    }

                count = VPNAccess.objects.count()
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                return {
                    "key": "vpn",
                    "name": "Enterprise VPN Gateway",
                    "mode": "Local simulation",
                    "is_simulated": True,
                    "is_live_external": False,
                    "status": "SIMULATED_HEALTHY",
                    "reachability": "Simulation Functional",
                    "latency_ms": duration_ms,
                    "message": f"Local VPN simulation adapter functional ({count} records in ORM). No live RADIUS server connected."
                }
            except Exception as exc:
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                return {
                    "key": "vpn",
                    "name": "Enterprise VPN Gateway",
                    "mode": "Local simulation",
                    "is_simulated": True,
                    "is_live_external": False,
                    "status": "ERROR",
                    "reachability": "Adapter Error",
                    "latency_ms": duration_ms,
                    "message": f"VPN connector error: {exc}"
                }

        elif key == 'github':
            try:
                adapter = ConnectorRegistry.get_connector('github')
                if getattr(adapter, 'token', None):
                    url = f"{adapter.base_url}/orgs/{adapter.org_name}"
                    req = urllib.request.Request(url, headers=adapter._get_headers(), method='GET')
                    try:
                        with urllib.request.urlopen(req, timeout=5) as resp:
                            duration_ms = round((time.perf_counter() - start) * 1000, 2)
                            return {
                                "key": "github",
                                "name": "GitHub Enterprise",
                                "mode": "Live external",
                                "is_simulated": False,
                                "is_live_external": True,
                                "status": "HEALTHY",
                                "reachability": "Live API Reachable",
                                "latency_ms": duration_ms,
                                "message": f"Live GitHub Enterprise API verified for org '{adapter.org_name}' (HTTP {resp.status})."
                            }
                    except urllib.error.HTTPError as exc:
                        duration_ms = round((time.perf_counter() - start) * 1000, 2)
                        return {
                            "key": "github",
                            "name": "GitHub Enterprise",
                            "mode": "Live external",
                            "is_simulated": False,
                            "is_live_external": True,
                            "status": "ERROR",
                            "reachability": f"API Error (HTTP {exc.code})",
                            "latency_ms": duration_ms,
                            "message": f"GitHub API responded with HTTP {exc.code}: {exc.reason}"
                        }
                    except urllib.error.URLError as exc:
                        duration_ms = round((time.perf_counter() - start) * 1000, 2)
                        is_timeout = "timed out" in str(exc.reason).lower()
                        return {
                            "key": "github",
                            "name": "GitHub Enterprise",
                            "mode": "Live external",
                            "is_simulated": False,
                            "is_live_external": True,
                            "status": "TIMEOUT" if is_timeout else "CONNECTION_FAILED",
                            "reachability": "Timeout (5s)" if is_timeout else "Network Failure",
                            "latency_ms": duration_ms,
                            "message": f"GitHub API connection failure: {exc.reason}"
                        }

                count = GitHubMembership.objects.count()
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                return {
                    "key": "github",
                    "name": "GitHub Enterprise",
                    "mode": "Database fallback",
                    "is_simulated": True,
                    "is_live_external": False,
                    "status": "DATABASE_FALLBACK_HEALTHY",
                    "reachability": "Database Fallback Active",
                    "latency_ms": duration_ms,
                    "message": f"Operating in database fallback mode ({count} membership records). GITHUB_ACCESS_TOKEN is not configured; no external API calls made."
                }
            except Exception as exc:
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                return {
                    "key": "github",
                    "name": "GitHub Enterprise",
                    "mode": "Database fallback",
                    "is_simulated": True,
                    "is_live_external": False,
                    "status": "ERROR",
                    "reachability": "Adapter Error",
                    "latency_ms": duration_ms,
                    "message": f"GitHub connector error: {exc}"
                }

        elif key == 'cloud':
            try:
                count = CloudIAMAccess.objects.count()
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                return {
                    "key": "cloud",
                    "name": "Cloud IAM (AWS)",
                    "mode": "Local simulation",
                    "is_simulated": True,
                    "is_live_external": False,
                    "status": "SIMULATED_HEALTHY",
                    "reachability": "Simulation Functional",
                    "latency_ms": duration_ms,
                    "message": f"Local Cloud IAM simulation adapter functional ({count} synthetic identity records). No live AWS STS/IAM APIs connected."
                }
            except Exception as exc:
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                return {
                    "key": "cloud",
                    "name": "Cloud IAM (AWS)",
                    "mode": "Local simulation",
                    "is_simulated": True,
                    "is_live_external": False,
                    "status": "ERROR",
                    "reachability": "Adapter Error",
                    "latency_ms": duration_ms,
                    "message": f"Cloud IAM connector error: {exc}"
                }

        elif key == 'slack':
            try:
                count = SlackAccount.objects.count()
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                return {
                    "key": "slack",
                    "name": "Slack Workspace",
                    "mode": "Local simulation",
                    "is_simulated": True,
                    "is_live_external": False,
                    "status": "SIMULATED_HEALTHY",
                    "reachability": "Simulation Functional",
                    "latency_ms": duration_ms,
                    "message": f"Local Slack simulation adapter functional ({count} synthetic account records). No live Slack Web API connected."
                }
            except Exception as exc:
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                return {
                    "key": "slack",
                    "name": "Slack Workspace",
                    "mode": "Local simulation",
                    "is_simulated": True,
                    "is_live_external": False,
                    "status": "ERROR",
                    "reachability": "Adapter Error",
                    "latency_ms": duration_ms,
                    "message": f"Slack connector error: {exc}"
                }

        else:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "key": key,
                "name": key.upper(),
                "status": "UNSUPPORTED",
                "reachability": "Unknown System",
                "latency_ms": duration_ms,
                "is_simulated": False,
                "is_live_external": False,
                "message": f"Unsupported connector system key '{key}'. Supported systems: hr, vpn, github, cloud, slack."
            }

    def get(self, request, system_key=None):
        if system_key:
            res = self._check_system(system_key, request=request)
            if res["status"] in ["ERROR", "CONNECTION_FAILED"]:
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            elif res["status"] == "TIMEOUT":
                status_code = status.HTTP_504_GATEWAY_TIMEOUT
            elif res["status"] == "UNSUPPORTED":
                status_code = status.HTTP_404_NOT_FOUND
            else:
                status_code = status.HTTP_200_OK
            return Response(res, status=status_code)

        results = {}
        for key in ['hr', 'vpn', 'github', 'cloud', 'slack']:
            results[key] = self._check_system(key, request=request)

        return Response({
            "status": "success",
            "systems": results
        }, status=status.HTTP_200_OK)

    def post(self, request, system_key=None):
        return self.get(request, system_key=system_key)

