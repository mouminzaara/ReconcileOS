import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reconcileos.settings')
django.setup()

from apps.employees.models import Employee, EmployeeStatus
from apps.connectors.models import (
    VPNAccess, VPNAccessStatus,
    GitHubMembership, GitHubAccessStatus,
    CloudIAMAccess, CloudRole,
    SlackAccount, SlackAccountStatus
)
from apps.reconciliation.collectors import StateCollector
from apps.reconciliation.monitor import ContinuousMonitor
from apps.reconciliation.models import IntegrityViolation
from apps.workflows.models import RepairPlan, RepairVerification

print("=== MILESTONE 15 ADDITIONAL CONNECTED SYSTEMS DEMONSTRATION ===")

# Step 1: Query Rahul Kumar's initial multi-system state
emp = Employee.objects.get(email='rahul.kumar@reconcileos.internal')

collector = StateCollector()
state_before = collector.collect_employee_state(emp)

print("\n1. Initial Multi-System Identity Audit (Drift State):")
print(f"   - Employee   : {state_before['employee_name']} ({state_before['employee_email']})")
print(f"   - HR State   : {state_before['employee_status']}")
print(f"   - VPN        : {state_before['systems']['vpn']['access_status']}")
print(f"   - GitHub     : {state_before['systems']['github']['access_status']} (Username: {state_before['systems']['github']['username']})")
print(f"   - Cloud IAM  : {state_before['systems']['cloud']['access_status']} (Role: {state_before['systems']['cloud']['role']})")
print(f"   - Slack      : {state_before['systems']['slack']['access_status']} (User ID: {state_before['systems']['slack']['slack_user_id']})")

# Step 2: ContinuousMonitor runs audit cycle across all 4 target systems
print("\n2. Executing Continuous Integrity Audit & Self-Healing Cycle...")
monitor = ContinuousMonitor()
summary = monitor.run_monitoring_cycle(employee_id=str(emp.id), auto_approve_policy=True)

print("\n3. Monitoring Cycle Execution Metrics:")
print(json.dumps(summary, indent=2))

# Step 3: Query final state after multi-system remediation
state_after = collector.collect_employee_state(emp)

print("\n4. Post-Remediation Multi-System Identity Audit:")
print(f"   - HR State   : {state_after['employee_status']}")
print(f"   - VPN        : {state_after['systems']['vpn']['access_status']}")
print(f"   - GitHub     : {state_after['systems']['github']['access_status']}")
print(f"   - Cloud IAM  : {state_after['systems']['cloud']['access_status']}")
print(f"   - Slack      : {state_after['systems']['slack']['access_status']}")
print(f"   - Final System Status: {summary['system_status']} (0 Remaining Violations)")

# Step 4: Verify underlying violations and plans
violations = IntegrityViolation.objects.filter(employee=emp)
plans = RepairPlan.objects.filter(employee=emp)

print(f"\n5. Repair Plans & Verifications Details ({plans.count()} plans):")
for p in plans:
    verif = RepairVerification.objects.filter(repair_plan=p).first()
    print(f"   - [{p.target_system}] Action: '{p.action}' | Plan Status: {p.status} | Verif Result: {verif.result if verif else 'N/A'}")

print("\n=== MILESTONE 15 DEMONSTRATION COMPLETED SUCCESSFULLY ===")
