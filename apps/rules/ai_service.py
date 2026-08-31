"""
AI-Assisted Rule Generation Service for ReconcileOS.

Converts natural-language security requirements into proposed structured invariant rules
in DRAFT state (is_enabled=False). Fully isolated from the deterministic reconciliation engine.
"""

import re
import uuid
import logging
from typing import Dict, Any
from django.core.exceptions import ValidationError
from .models import Rule, RuleSeverity
from apps.audit.services import AuditLogger
from apps.audit.models import AuditEventType

logger = logging.getLogger(__name__)


class AIRuleGenerationException(Exception):
    """Raised when natural language prompt cannot be parsed into a valid security invariant rule."""
    pass


class AIRuleGenerator:
    """
    Isolated AI Rule Generator Service.

    Parses natural language requirements into structured DRAFT rules (is_enabled=False).
    AI components NEVER directly activate rules, modify downstream systems, or execute repairs.
    """

    @staticmethod
    def parse_prompt(prompt: str) -> Dict[str, Any]:
        """
        Parses a natural language requirement string into structured rule parameters.

        Args:
            prompt (str): Natural language policy prompt (e.g. "Terminated employees must not have access to VPN").

        Returns:
            Dict[str, Any]: Extracted rule parameters matching Rule model fields.

        Raises:
            AIRuleGenerationException: If prompt is invalid or unparseable.
        """
        if not prompt or not isinstance(prompt, str) or len(prompt.strip()) < 10:
            raise AIRuleGenerationException(
                "Prompt is too short or invalid. Please provide a clear natural language requirement."
            )

        clean_prompt = prompt.strip()
        prompt_upper = clean_prompt.upper()

        # Check for gibberish or non-sensical inputs
        valid_keywords = ['TERMINATED', 'EMPLOYEE', 'ACCESS', 'VPN', 'GITHUB', 'CLOUD', 'SLACK', 'REVOKE', 'DISABLE', 'REMOVE', 'SYSTEM']
        if not any(kw in prompt_upper for kw in valid_keywords):
            raise AIRuleGenerationException(
                "Unable to extract a valid security invariant rule from prompt. "
                "Please specify source employee condition and target system requirement."
            )

        # 1. Extract Source Condition Value
        condition_value = 'TERMINATED'
        if 'LEAVE' in prompt_upper or 'ON LEAVE' in prompt_upper:
            condition_value = 'ON_LEAVE'
        elif 'INACTIVE' in prompt_upper:
            condition_value = 'INACTIVE'

        # 2. Extract Target System & Expectation
        target_system = 'VPN'
        expected_attribute = 'status'
        expected_value = 'DISABLED'

        if 'GITHUB' in prompt_upper or 'GIT' in prompt_upper:
            target_system = 'GITHUB'
            expected_attribute = 'status'
            expected_value = 'REVOKED' if ('REVOKE' in prompt_upper or 'REVOKED' in prompt_upper) else 'NOT_MEMBER'
        elif 'CLOUD' in prompt_upper or 'IAM' in prompt_upper or 'AWS' in prompt_upper:
            target_system = 'CLOUD'
            expected_attribute = 'role'
            expected_value = 'NO_ROLE' if ('NO ROLE' in prompt_upper or 'REVOKE' in prompt_upper) else 'NO_ROLE'
        elif 'SLACK' in prompt_upper:
            target_system = 'SLACK'
            expected_attribute = 'status'
            expected_value = 'DEACTIVATED' if ('DEACTIVAT' in prompt_upper) else 'DISABLED'
        elif 'VPN' in prompt_upper:
            target_system = 'VPN'
            expected_attribute = 'status'
            expected_value = 'DISABLED'
        elif 'SYSTEM' in prompt_upper or 'COMPANY' in prompt_upper:
            target_system = 'VPN'
            expected_attribute = 'status'
            expected_value = 'DISABLED'

        # 3. Extract Severity
        severity = RuleSeverity.HIGH
        if 'CRITICAL' in prompt_upper or 'URGENT' in prompt_upper or 'MUST NOT' in prompt_upper:
            severity = RuleSeverity.CRITICAL
        elif 'MEDIUM' in prompt_upper:
            severity = RuleSeverity.MEDIUM
        elif 'LOW' in prompt_upper:
            severity = RuleSeverity.LOW

        # Generate unique rule code
        code_suffix = uuid.uuid4().hex[:6].upper()
        rule_code = f"AI-DRAFT-{code_suffix}"

        rule_name = f"AI Proposed: {target_system} Invariant ({condition_value} -> {expected_value})"
        description = (
            f"AI-generated draft invariant rule derived from administrator prompt: \"{clean_prompt}\". "
            f"Requires explicit human administrator review and activation before evaluation."
        )

        return {
            'rule_code': rule_code,
            'name': rule_name,
            'description': description,
            'source_system': 'HR',
            'condition_attribute': 'status',
            'condition_value': condition_value,
            'target_system': target_system,
            'expected_attribute': expected_attribute,
            'expected_value': expected_value,
            'severity': severity,
            'is_enabled': False,  # STRICTLY DRAFT
        }

    @classmethod
    def generate_draft_rule(cls, prompt: str, creator_actor: str = 'SYSTEM') -> Rule:
        """
        Parses natural language prompt and persists a new Rule strictly in DRAFT state (is_enabled=False).

        Args:
            prompt (str): Natural language rule specification.
            creator_actor (str): Identifier of administrator submitting prompt.

        Returns:
            Rule: The created DRAFT rule instance.
        """
        params = cls.parse_prompt(prompt)

        rule = Rule.objects.create(
            rule_code=params['rule_code'],
            name=params['name'],
            description=params['description'],
            source_system=params['source_system'],
            condition_attribute=params['condition_attribute'],
            condition_value=params['condition_value'],
            target_system=params['target_system'],
            expected_attribute=params['expected_attribute'],
            expected_value=params['expected_value'],
            severity=params['severity'],
            is_enabled=False  # Always DRAFT on creation
        )

        logger.info(
            f"Generated AI draft rule {rule.rule_code} [{rule.name}] from prompt. Status: DRAFT (is_enabled=False)."
        )

        try:
            AuditLogger.log_event(
                event_type=AuditEventType.RULE_EVALUATED,
                actor=creator_actor,
                system=rule.target_system,
                action='GENERATE_AI_DRAFT_RULE',
                previous_state='PROMPT',
                new_state='DRAFT_RULE',
                result='DRAFT_CREATED',
                additional_metadata={
                    'rule_id': str(rule.id),
                    'rule_code': rule.rule_code,
                    'prompt': prompt,
                    'is_enabled': False
                }
            )
        except Exception as e:
            logger.warning(f"Could not log audit event for AI rule generation: {e}")

        return rule
