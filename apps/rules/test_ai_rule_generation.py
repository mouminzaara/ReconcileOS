"""
Unit and Integration Tests for ReconcileOS AI-Assisted Rule Generation.
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Rule, RuleSeverity
from .ai_service import AIRuleGenerator, AIRuleGenerationException
from apps.accounts.models import UserProfile, UserRole
from apps.employees.models import Employee
from apps.connectors.models import VPNAccess, VPNAccessStatus
from apps.reconciliation.engine import ReconciliationEngine
from apps.reconciliation.models import IntegrityViolation


class AIRuleGeneratorServiceTests(TestCase):
    """Unit tests for AIRuleGenerator prompt parsing and safety constraints."""

    def test_parse_valid_vpn_prompt(self):
        prompt = "Terminated employees must not have access to company VPN system"
        params = AIRuleGenerator.parse_prompt(prompt)

        self.assertEqual(params['source_system'], 'HR')
        self.assertEqual(params['condition_attribute'], 'status')
        self.assertEqual(params['condition_value'], 'TERMINATED')
        self.assertEqual(params['target_system'], 'VPN')
        self.assertEqual(params['expected_attribute'], 'status')
        self.assertEqual(params['expected_value'], 'DISABLED')
        self.assertFalse(params['is_enabled'])  # MUST BE DRAFT

    def test_parse_valid_github_prompt(self):
        prompt = "Revoke GitHub access for terminated employees immediately"
        params = AIRuleGenerator.parse_prompt(prompt)

        self.assertEqual(params['target_system'], 'GITHUB')
        self.assertFalse(params['is_enabled'])

    def test_parse_valid_cloud_prompt(self):
        prompt = "Employees on leave must have Cloud IAM role set to NO_ROLE"
        params = AIRuleGenerator.parse_prompt(prompt)

        self.assertEqual(params['condition_value'], 'ON_LEAVE')
        self.assertEqual(params['target_system'], 'CLOUD')
        self.assertEqual(params['expected_attribute'], 'role')
        self.assertEqual(params['expected_value'], 'NO_ROLE')
        self.assertFalse(params['is_enabled'])

    def test_parse_invalid_prompts_raise_exception(self):
        invalid_prompts = [
            "",
            "   ",
            "hello",
            "foo bar baz",
            "1234567890",
            "!@#$%^&*()_+",
        ]

        for bad_prompt in invalid_prompts:
            with self.assertRaises(AIRuleGenerationException):
                AIRuleGenerator.parse_prompt(bad_prompt)

    def test_generate_draft_rule_saves_disabled_instance(self):
        prompt = "Terminated employees must not have access to Slack"
        rule = AIRuleGenerator.generate_draft_rule(prompt, creator_actor="admin_test")

        self.assertIsNotNone(rule.id)
        self.assertTrue(rule.rule_code.startswith("AI-DRAFT-"))
        self.assertFalse(rule.is_enabled)  # DRAFT STATUS ENFORCED
        self.assertEqual(rule.target_system, "SLACK")


class AIRuleGenerationAPITests(APITestCase):
    """Integration tests for AI rule generation REST API endpoint."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin_ai', 'admin@ai.com', 'admin123')
        UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)
        self.client.force_authenticate(user=self.admin_user)
        self.generate_url = reverse('rule-generate-draft')

    def test_generate_draft_api_success(self):
        payload = {
            "prompt": "Terminated employees must not have access to company systems"
        }
        response = self.client.post(self.generate_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertFalse(response.data['is_enabled'])
        self.assertTrue(response.data['human_review_required'])
        self.assertTrue(response.data['rule']['rule_code'].startswith('AI-DRAFT-'))

    def test_generate_draft_api_invalid_prompt(self):
        payload = {
            "prompt": "hello world"
        }
        response = self.client.post(self.generate_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertFalse(response.data['human_review_required'])

    def test_draft_rule_isolation_from_reconciliation_engine(self):
        # 1. Create employee in TERMINATED state with ENABLED VPN access (Drift state)
        employee = Employee.objects.create(
            full_name="David Miller",
            email="david@example.com",
            department="Engineering",
            status="TERMINATED"
        )
        VPNAccess.objects.create(
            employee=employee,
            status=VPNAccessStatus.ENABLED
        )

        # 2. Generate AI Draft Rule (is_enabled=False)
        payload = {
            "prompt": "Terminated employees must not have access to VPN"
        }
        resp = self.client.post(self.generate_url, payload, format='json')
        rule_id = resp.data['rule']['id']
        draft_rule = Rule.objects.get(pk=rule_id)
        self.assertFalse(draft_rule.is_enabled)

        # 3. Evaluate Reconciliation Engine -> Draft rule MUST BE IGNORED!
        engine = ReconciliationEngine()
        report = engine.evaluate_employee_rules(employee)
        self.assertEqual(report['violations_detected_count'], 0)
        self.assertFalse(IntegrityViolation.objects.filter(employee=employee, rule=draft_rule).exists())

        # 4. Human Review & Explicit Activation (Toggle rule)
        toggle_url = reverse('rule-toggle', kwargs={'pk': draft_rule.pk})
        toggle_resp = self.client.post(toggle_url)
        self.assertTrue(toggle_resp.data['is_enabled'])
        draft_rule.refresh_from_db()
        self.assertTrue(draft_rule.is_enabled)

        # 5. Evaluate Reconciliation Engine -> Now activated rule detects violation!
        report_active = engine.evaluate_employee_rules(employee)
        self.assertEqual(report_active['violations_detected_count'], 1)
        self.assertTrue(IntegrityViolation.objects.filter(employee=employee, rule=draft_rule).exists())
