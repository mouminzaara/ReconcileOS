"""
Continuous Integrity Monitoring Engine for ReconcileOS.

Periodically checks whether invariant rules remain satisfied across downstream systems.
Detects post-repair authorization drift and reuses the existing self-healing pipeline
(Detection -> Planning -> Approval -> Execution -> Verification).
"""

import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from django.db.models import Q

from apps.employees.models import Employee
from apps.reconciliation.models import IntegrityViolation, ViolationStatus
from apps.reconciliation.engine import ReconciliationEngine
from apps.reconciliation.collectors import StateCollector
from apps.workflows.planner import RepairPlanner
from apps.workflows.executor import RepairExecutor
from apps.workflows.verifier import PostRepairVerifier
from apps.workflows.models import RepairPlan, PlanStatus, RepairVerification, VerificationResult
from apps.approvals.models import ApprovalRequest, ApprovalDecision
from apps.approvals.services import ApprovalService

logger = logging.getLogger(__name__)


class ContinuousMonitor:
    """
    Continuous Integrity Monitoring Engine.

    Executes automated monitoring cycles to evaluate active invariant rules, detect
    unauthorized drift, and drive self-healing via existing ReconcileOS architecture.
    """

    def __init__(
        self,
        state_collector: Optional[StateCollector] = None,
        engine: Optional[ReconciliationEngine] = None,
        planner: Optional[RepairPlanner] = None,
        executor: Optional[RepairExecutor] = None,
        verifier: Optional[PostRepairVerifier] = None
    ):
        self.state_collector = state_collector or StateCollector()
        self.engine = engine or ReconciliationEngine(state_collector=self.state_collector)
        self.planner = planner or RepairPlanner()
        self.executor = executor or RepairExecutor(state_collector=self.state_collector)
        self.verifier = verifier or PostRepairVerifier(state_collector=self.state_collector)

    def run_monitoring_cycle(
        self,
        employee_id: Optional[str] = None,
        auto_approve_policy: bool = False
    ) -> Dict[str, Any]:
        """
        Executes a complete continuous integrity monitoring cycle:
        1. Evaluate active invariant rules across target employees.
        2. Collect multi-system state & detect authorization drift.
        3. Generate deterministic repair plans for open violations.
        4. Process approvals according to policy.
        5. Execute eligible approved repair plans via connector abstraction.
        6. Perform empirical post-repair verification.

        Returns:
            Dict containing detailed cycle execution metrics and status summary.
        """
        cycle_start_time = timezone.now()
        logger.info(f"Starting Continuous Integrity Monitoring Cycle at {cycle_start_time.isoformat()}...")

        # 1. Audit & Detect Drift (Reconciliation Engine)
        if employee_id:
            eval_results = [self.engine.evaluate_employee_rules(employee_id)]
            employees_evaluated_count = 1
        else:
            eval_results = self.engine.evaluate_all_rules()
            employees_evaluated_count = Employee.objects.count()

        # Query all active OPEN violations
        open_violations_qs = IntegrityViolation.objects.filter(status=ViolationStatus.OPEN)
        if employee_id:
            open_violations_qs = open_violations_qs.filter(employee_id=employee_id)
        open_violations = list(open_violations_qs)

        violations_detected_count = len(open_violations)
        logger.info(f"Monitoring cycle detected {violations_detected_count} open integrity violation(s).")

        # 2. Repair Planning
        plans_generated = []
        for violation in open_violations:
            try:
                plan, created = self.planner.plan_for_violation(violation)
                plans_generated.append(plan)
            except Exception as exc:
                logger.error(f"Error generating repair plan for violation {violation.id}: {exc}")

        # 3. Approval Processing
        approvals_processed_count = 0
        for plan in plans_generated:
            approval_req = ApprovalRequest.objects.filter(repair_plan=plan).first()
            if approval_req and approval_req.decision == ApprovalDecision.PENDING:
                if auto_approve_policy:
                    try:
                        ApprovalService.approve_request(
                            approval_req,
                            comment="Auto-approved by Continuous Integrity Monitoring Policy"
                        )
                        approvals_processed_count += 1
                        logger.info(f"Auto-approved repair plan {plan.id} for {plan.employee.full_name}.")
                    except Exception as exc:
                        logger.error(f"Failed to auto-approve repair plan {plan.id}: {exc}")

        # 4. Repair Execution & Verification
        repairs_executed_count = 0
        verifications_completed_count = 0

        # Query plans eligible for execution (APPROVED or RETRYING)
        executable_plans_qs = RepairPlan.objects.filter(
            id__in=[p.id for p in plans_generated],
            status__in=[PlanStatus.APPROVED, PlanStatus.RETRYING]
        )

        for plan in executable_plans_qs:
            try:
                log = self.executor.execute_plan(plan, auto_retry=True)
                repairs_executed_count += 1

                # Check if verification succeeded
                verification = RepairVerification.objects.filter(repair_plan=plan).first()
                if verification and verification.result == VerificationResult.VERIFIED:
                    verifications_completed_count += 1
            except Exception as exc:
                logger.error(f"Error executing repair plan {plan.id} during monitoring cycle: {exc}")

        # Final state check
        remaining_open_violations = IntegrityViolation.objects.filter(status=ViolationStatus.OPEN)
        if employee_id:
            remaining_open_violations = remaining_open_violations.filter(employee_id=employee_id)
        remaining_count = remaining_open_violations.count()

        system_status = "CONSISTENT" if remaining_count == 0 else "DRIFT_DETECTED"
        cycle_end_time = timezone.now()

        summary = {
            "cycle_start_time": cycle_start_time.isoformat(),
            "cycle_completed_time": cycle_end_time.isoformat(),
            "duration_seconds": round((cycle_end_time - cycle_start_time).total_seconds(), 3),
            "employees_evaluated_count": employees_evaluated_count,
            "violations_detected_count": violations_detected_count,
            "repair_plans_generated_count": len(plans_generated),
            "approvals_processed_count": approvals_processed_count,
            "repairs_executed_count": repairs_executed_count,
            "verifications_completed_count": verifications_completed_count,
            "remaining_open_violations_count": remaining_count,
            "system_status": system_status
        }

        logger.info(f"Completed Continuous Monitoring Cycle: Status={system_status}, Remaining Violations={remaining_count}.")
        return summary
