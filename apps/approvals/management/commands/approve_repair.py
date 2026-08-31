"""
Django management command to approve or reject Repair Plans via CLI.
"""

import json
from django.core.management.base import BaseCommand
from apps.approvals.models import ApprovalRequest, ApprovalDecision
from apps.approvals.services import ApprovalService
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Approves or rejects a pending repair plan.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--plan-id',
            type=str,
            help='UUID of the repair plan to approve/reject.'
        )
        parser.add_argument(
            '--action',
            type=str,
            choices=['approve', 'reject', 'list'],
            default='list',
            help='Action to perform: approve, reject, or list pending approvals (default: list).'
        )
        parser.add_argument(
            '--comment',
            type=str,
            default='',
            help='Optional rationale/comment for the decision.'
        )

    def handle(self, *args, **options):
        action = options.get('action')
        plan_id = options.get('plan_id')
        comment = options.get('comment', '')

        self.stdout.write(self.style.MIGRATE_HEADING("=== ReconcileOS Human-in-the-Loop Approvals Engine ==="))

        if action == 'list' or not plan_id:
            pending_requests = ApprovalRequest.objects.filter(decision=ApprovalDecision.PENDING)
            self.stdout.write(self.style.SUCCESS(f"\nPending Approval Requests: ({pending_requests.count()})"))

            results = []
            for req in pending_requests:
                results.append({
                    "approval_id": str(req.id),
                    "repair_plan_id": str(req.repair_plan_id),
                    "employee": req.repair_plan.employee.full_name,
                    "target_system": req.repair_plan.target_system,
                    "action": req.repair_plan.action,
                    "risk_level": req.repair_plan.risk_level,
                    "decision": req.decision,
                    "created_at": req.created_at.isoformat()
                })
            self.stdout.write(json.dumps(results, indent=2))
            return

        # Find approval request for plan_id or request id
        req = (
            ApprovalRequest.objects.filter(repair_plan_id=plan_id).first() or
            ApprovalRequest.objects.filter(id=plan_id).first()
        )

        if not req:
            self.stdout.write(self.style.ERROR(f"No approval request found for ID '{plan_id}'."))
            return

        try:
            if action == 'approve':
                ApprovalService.approve_request(req, comment=comment)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n[APPROVED] Repair Plan {req.repair_plan.id} for {req.repair_plan.employee.full_name} is now APPROVED."
                    )
                )
            elif action == 'reject':
                ApprovalService.reject_request(req, comment=comment)
                self.stdout.write(
                    self.style.WARNING(
                        f"\n[REJECTED] Repair Plan {req.repair_plan.id} for {req.repair_plan.employee.full_name} is now REJECTED."
                    )
                )

            req.refresh_from_db()
            self.stdout.write(json.dumps({
                "approval_id": str(req.id),
                "repair_plan_id": str(req.repair_plan_id),
                "plan_status": req.repair_plan.status,
                "decision": req.decision,
                "decided_at": req.decided_at.isoformat() if req.decided_at else None,
                "comment": req.comment
            }, indent=2))
        except ValidationError as exc:
            self.stdout.write(self.style.ERROR(f"Error: {exc}"))
