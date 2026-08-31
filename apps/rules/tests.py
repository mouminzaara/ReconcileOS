"""
Automated unit and integration test suite for ReconcileOS Invariant Rule Engine.
"""

import uuid
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Rule, RuleSeverity
from apps.accounts.models import UserProfile, UserRole


class RuleModelTests(TestCase):
    """Unit tests for the Rule model methods and constraints."""

    def setUp(self):
        self.rule = Rule.objects.create(
            rule_code="INV-TEST-001",
            name="Terminated employee VPN disabled test rule",
            description="Test description for VPN invariant rule",
            source_system="HR",
            condition_attribute="status",
            condition_value="TERMINATED",
            target_system="VPN",
            expected_attribute="status",
            expected_value="DISABLED",
            severity=RuleSeverity.CRITICAL,
            is_enabled=True
        )

    def test_rule_creation_defaults_and_str(self):
        """Test rule fields, UUID primary key, and __str__ representation."""
        self.assertIsInstance(self.rule.id, uuid.UUID)
        self.assertEqual(self.rule.rule_code, "INV-TEST-001")
        self.assertEqual(self.rule.severity, RuleSeverity.CRITICAL)
        self.assertTrue(self.rule.is_enabled)
        self.assertIn("INV-TEST-001", str(self.rule))
        self.assertIn("HR -> VPN", str(self.rule))

    def test_matches_condition(self):
        """Test matches_condition helper evaluates source values correctly."""
        self.assertTrue(self.rule.matches_condition("TERMINATED"))
        self.assertTrue(self.rule.matches_condition("terminated"))
        self.assertTrue(self.rule.matches_condition(" TERMINATED "))
        self.assertFalse(self.rule.matches_condition("ACTIVE"))
        self.assertFalse(self.rule.matches_condition(None))

    def test_evaluates_drift(self):
        """Test evaluates_drift identifies authorization drift correctly."""
        self.assertTrue(self.rule.evaluates_drift("TERMINATED", "ENABLED"))
        self.assertFalse(self.rule.evaluates_drift("TERMINATED", "DISABLED"))
        self.assertFalse(self.rule.evaluates_drift("ACTIVE", "ENABLED"))

        self.rule.is_enabled = False
        self.rule.save()
        self.assertFalse(self.rule.evaluates_drift("TERMINATED", "ENABLED"))


class RuleAPITests(APITestCase):
    """Integration tests for Rule REST API endpoints."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin_rules', 'admin@rules.com', 'admin123')
        UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)
        self.client.force_authenticate(user=self.admin_user)

        self.rule1 = Rule.objects.create(
            rule_code="INV-RULE-001",
            name="Terminated VPN disabled",
            source_system="HR",
            condition_attribute="status",
            condition_value="TERMINATED",
            target_system="VPN",
            expected_attribute="status",
            expected_value="DISABLED",
            severity=RuleSeverity.CRITICAL,
            is_enabled=True
        )
        self.rule2 = Rule.objects.create(
            rule_code="INV-RULE-002",
            name="Terminated GitHub revoked",
            source_system="HR",
            condition_attribute="status",
            condition_value="TERMINATED",
            target_system="GitHub",
            expected_attribute="status",
            expected_value="REVOKED",
            severity=RuleSeverity.HIGH,
            is_enabled=False
        )

        self.list_url = reverse('rule-list')
        self.detail_url1 = reverse('rule-detail', kwargs={'pk': self.rule1.pk})

    def test_list_rules(self):
        """Test GET /api/v1/rules/ lists all rules with rule_expression."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertIn("WHEN HR.status == 'TERMINATED'", response.data['results'][0]['rule_expression'])

    def test_filter_rules_by_is_enabled_and_severity(self):
        """Test filtering rules endpoint by active status and severity."""
        response = self.client.get(f"{self.list_url}?is_enabled=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['rule_code'], 'INV-RULE-001')

        response = self.client.get(f"{self.list_url}?severity=HIGH")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['rule_code'], 'INV-RULE-002')

    def test_create_rule_api(self):
        """Test POST /api/v1/rules/ creates a new invariant rule."""
        payload = {
            "rule_code": "INV-RULE-003",
            "name": "Cloud Admin restriction",
            "description": "Restrict Cloud Admin role",
            "source_system": "HR",
            "condition_attribute": "status",
            "condition_value": "TERMINATED",
            "target_system": "Cloud",
            "expected_attribute": "status",
            "expected_value": "REVOKED",
            "severity": "CRITICAL",
            "is_enabled": True
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rule_code'], "INV-RULE-003")
        self.assertTrue(Rule.objects.filter(rule_code="INV-RULE-003").exists())

    def test_toggle_rule_action_endpoint(self):
        """Test POST /api/v1/rules/<id>/toggle/ toggles the is_enabled state."""
        toggle_url = reverse('rule-toggle', kwargs={'pk': self.rule1.pk})
        
        response = self.client.post(toggle_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_enabled'])
        self.rule1.refresh_from_db()
        self.assertFalse(self.rule1.is_enabled)

        response = self.client.post(toggle_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_enabled'])
        self.rule1.refresh_from_db()
        self.assertTrue(self.rule1.is_enabled)
