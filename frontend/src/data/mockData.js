/**
 * Centralized mock data repository for ReconcileOS Frontend Shell.
 * Designed to mirror future Django REST API payload structures.
 */

export const mockStats = {
  totalEmployees: 6,
  activeViolations: 2,
  pendingRepairs: 1,
  successfulReconciliations: 14,
  systemHealthPercent: 92,
  lastScanTimestamp: "2 mins ago"
};

export const mockConnectedSystems = [
  {
    id: "sys-hr",
    name: "HR System of Record",
    key: "HR",
    type: "Primary HRIS",
    protocol: "REST API / Webhook",
    status: "HEALTHY",
    lastChecked: "Just now",
    latency: "18 ms",
    icon: "Users",
    description: "Source of truth for employee identity, status, and lifecycle transitions.",
    activeAccounts: 6,
    driftCount: 0
  },
  {
    id: "sys-vpn",
    name: "Enterprise VPN Gateway",
    key: "VPN",
    type: "Access Control",
    protocol: "RADIUS / OpenVPN API",
    status: "DRIFT_DETECTED",
    lastChecked: "1 min ago",
    latency: "42 ms",
    icon: "ShieldAlert",
    description: "Simulated downstream VPN connector managing network access tokens.",
    activeAccounts: 5,
    driftCount: 1
  },
  {
    id: "sys-github",
    name: "GitHub Enterprise",
    key: "GitHub",
    type: "Version Control / SSO",
    protocol: "SCIM / REST API v3",
    status: "DRIFT_DETECTED",
    lastChecked: "3 mins ago",
    latency: "65 ms",
    icon: "GitBranch",
    description: "Manages developer organization memberships, repositories, and SSH keys.",
    activeAccounts: 5,
    driftCount: 1
  },
  {
    id: "sys-cloud",
    name: "Cloud IAM (AWS / GCP)",
    key: "Cloud",
    type: "Infrastructure Access",
    protocol: "AWS STS / Identity Center",
    status: "HEALTHY",
    lastChecked: "5 mins ago",
    latency: "31 ms",
    icon: "Cloud",
    description: "Production cloud role allocations, policy assignments, and credentials.",
    activeAccounts: 4,
    driftCount: 0
  },
  {
    id: "sys-slack",
    name: "Slack Workspace",
    key: "Slack",
    type: "Collaboration",
    protocol: "Slack Admin API",
    status: "HEALTHY",
    lastChecked: "4 mins ago",
    latency: "25 ms",
    icon: "MessageSquare",
    description: "Enterprise workspace user profiles, guest accounts, and channel permissions.",
    activeAccounts: 6,
    driftCount: 0
  }
];

export const mockLifecycleSteps = [
  { id: "step-1", name: "Detected", status: "completed", timestamp: "10:14:02 AM", description: "Drift detected via rule evaluation" },
  { id: "step-2", name: "Planned", status: "completed", timestamp: "10:14:05 AM", description: "Remediation plan generated" },
  { id: "step-3", name: "Approval", status: "in-progress", timestamp: "10:15:00 AM", description: "Human approval pending (SecOps)" },
  { id: "step-4", name: "Execution", status: "pending", timestamp: "--:--:--", description: "Automated API repair action" },
  { id: "step-5", name: "Verification", status: "pending", timestamp: "--:--:--", description: "Post-reconciliation state audit" }
];

export const mockViolations = [
  {
    id: "VIO-2026-001",
    employeeName: "Rahul Kumar",
    employeeEmail: "rahul.kumar@reconcileos.internal",
    employeeDepartment: "DevOps & Cloud Integrity",
    hrStatus: "TERMINATED",
    systemKey: "VPN",
    systemName: "Enterprise VPN Gateway",
    ruleId: "INV-RULE-001",
    ruleName: "Terminated employees must not have VPN access",
    expectedState: "DISABLED",
    actualState: "ENABLED",
    severity: "CRITICAL",
    status: "ACTIVE",
    detectedAt: "2026-08-28 10:14:02 IST",
    repairId: "REP-8042"
  },
  {
    id: "VIO-2026-002",
    employeeName: "David Miller",
    employeeEmail: "david.miller@reconcileos.internal",
    employeeDepartment: "Finance & Operations",
    hrStatus: "TERMINATED",
    systemKey: "GitHub",
    systemName: "GitHub Enterprise",
    ruleId: "INV-RULE-002",
    ruleName: "Terminated employees must not retain GitHub Org Membership",
    expectedState: "REVOKED",
    actualState: "ACTIVE_MEMBER",
    severity: "HIGH",
    status: "ACTIVE",
    detectedAt: "2026-08-28 09:30:15 IST",
    repairId: "REP-8043"
  },
  {
    id: "VIO-2026-003",
    employeeName: "Elena Rostova",
    employeeEmail: "elena.rostova@reconcileos.internal",
    employeeDepartment: "Product Engineering",
    hrStatus: "ACTIVE",
    systemKey: "Cloud",
    systemName: "Cloud IAM (AWS / GCP)",
    ruleId: "INV-RULE-003",
    ruleName: "Non-Infrastructure staff must not hold AdministratorAccess",
    expectedState: "READ_ONLY",
    actualState: "ADMINISTRATOR_FULL",
    severity: "MEDIUM",
    status: "RESOLVED",
    detectedAt: "2026-08-27 16:45:10 IST",
    repairId: "REP-8040"
  }
];

export const mockEmployees = [
  {
    id: "e9f0d1a2-3b4c-5d6e-7f8a-9b0c1d2e3f4a",
    fullName: "Alice Johnson",
    email: "alice.johnson@reconcileos.internal",
    department: "Security & Identity",
    status: "ACTIVE",
    createdAt: "2026-01-15",
    systemsConnected: ["HR", "VPN", "GitHub", "Cloud", "Slack"]
  },
  {
    id: "b1c2d3e4-5f6a-7b8c-9d0e-1f2a3b4c5d6e",
    fullName: "Bob Smith",
    email: "bob.smith@reconcileos.internal",
    department: "Platform Engineering",
    status: "ACTIVE",
    createdAt: "2026-02-01",
    systemsConnected: ["HR", "VPN", "GitHub", "Cloud", "Slack"]
  },
  {
    id: "c3d4e5f6-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
    fullName: "Carol Danvers",
    email: "carol.danvers@reconcileos.internal",
    department: "DevOps & Infrastructure",
    status: "ACTIVE",
    createdAt: "2026-02-10",
    systemsConnected: ["HR", "VPN", "GitHub", "Cloud", "Slack"]
  },
  {
    id: "d5e6f7a8-9b0c-1d2e-3f4a-5b6c7d8e9f0a",
    fullName: "David Miller",
    email: "david.miller@reconcileos.internal",
    department: "Finance & Operations",
    status: "TERMINATED",
    createdAt: "2026-03-01",
    systemsConnected: ["HR", "GitHub"]
  },
  {
    id: "e7f8a9b0-1c2d-3e4f-5a6b-7c8d9e0f1a2b",
    fullName: "Elena Rostova",
    email: "elena.rostova@reconcileos.internal",
    department: "Product Engineering",
    status: "ACTIVE",
    createdAt: "2026-03-12",
    systemsConnected: ["HR", "VPN", "GitHub", "Cloud", "Slack"]
  },
  {
    id: "f9a0b1c2-3d4e-5f6a-7b8c-9d0e1f2a3b4c",
    fullName: "Rahul Kumar",
    email: "rahul.kumar@reconcileos.internal",
    department: "DevOps & Cloud Integrity",
    status: "TERMINATED",
    createdAt: "2026-04-05",
    systemsConnected: ["HR", "VPN", "GitHub", "Cloud"]
  }
];

export const mockRules = [
  {
    id: "INV-RULE-001",
    name: "Terminated employees must not have VPN access",
    description: "Whenever an employee status transitions to TERMINATED in the HR system of record, VPN access across all RADIUS/OpenVPN nodes must be immediately set to DISABLED.",
    targetSystems: ["HR", "VPN"],
    severity: "CRITICAL",
    status: "ENFORCED",
    lastEvaluated: "1 min ago",
    evaluationCount: 1420
  },
  {
    id: "INV-RULE-002",
    name: "Terminated employees must not retain GitHub Org Access",
    description: "Terminated employees must be removed from all private GitHub repositories and enterprise organizations within 15 minutes of HR status change.",
    targetSystems: ["HR", "GitHub"],
    severity: "HIGH",
    status: "ENFORCED",
    lastEvaluated: "3 mins ago",
    evaluationCount: 1420
  },
  {
    id: "INV-RULE-003",
    name: "Non-Infrastructure staff must not hold AdministratorAccess",
    description: "Enforces principle of least privilege. Administrator IAM policies in AWS/GCP are strictly restricted to verified DevOps & Security department members.",
    targetSystems: ["HR", "Cloud"],
    severity: "HIGH",
    status: "ENFORCED",
    lastEvaluated: "5 mins ago",
    evaluationCount: 890
  },
  {
    id: "INV-RULE-004",
    name: "Inactive accounts (>90 days) must be automatically suspended",
    description: "Identifies accounts with no interactive login activity for 90 days and revokes active tokens across downstream applications.",
    targetSystems: ["VPN", "Cloud", "Slack"],
    severity: "MEDIUM",
    status: "DRY_RUN",
    lastEvaluated: "10 mins ago",
    evaluationCount: 650
  }
];

export const mockRepairs = [
  {
    id: "REP-8042",
    employeeName: "Rahul Kumar",
    employeeEmail: "rahul.kumar@reconcileos.internal",
    targetSystem: "Enterprise VPN Gateway",
    systemKey: "VPN",
    action: "REVOKE_VPN_ACCESS",
    actionDetails: "Disable client certificate & set VPNAccess.status = DISABLED",
    reason: "HR status is TERMINATED (Invariant Rule #INV-RULE-001 violation)",
    status: "PENDING_APPROVAL",
    riskLevel: "CRITICAL",
    createdAt: "2026-08-28 10:15:00 IST"
  },
  {
    id: "REP-8043",
    employeeName: "David Miller",
    employeeEmail: "david.miller@reconcileos.internal",
    targetSystem: "GitHub Enterprise",
    systemKey: "GitHub",
    action: "REMOVE_ORG_MEMBER",
    actionDetails: "DELETE /orgs/reconcileos-enterprise/members/david-miller",
    reason: "HR status is TERMINATED (Invariant Rule #INV-RULE-002 violation)",
    status: "EXECUTING",
    riskLevel: "HIGH",
    createdAt: "2026-08-28 09:31:00 IST"
  },
  {
    id: "REP-8040",
    employeeName: "Elena Rostova",
    employeeEmail: "elena.rostova@reconcileos.internal",
    targetSystem: "Cloud IAM (AWS / GCP)",
    systemKey: "Cloud",
    action: "DEMOTE_IAM_ROLE",
    actionDetails: "Detach Policy: AdministratorAccess -> Attach Policy: DeveloperReadOnly",
    reason: "Department is Product Engineering (Invariant Rule #INV-RULE-003 violation)",
    status: "SUCCESS",
    riskLevel: "MEDIUM",
    createdAt: "2026-08-27 16:50:00 IST"
  }
];

export const mockApprovals = [
  {
    id: "APR-1092",
    repairId: "REP-8042",
    employeeName: "Rahul Kumar",
    employeeEmail: "rahul.kumar@reconcileos.internal",
    department: "DevOps & Cloud Integrity",
    requestedAction: "Revoke VPN Access & Invalidate Session Tokens",
    targetSystem: "VPN Gateway",
    riskLevel: "CRITICAL",
    reason: "HR record changed to TERMINATED. Active VPN connection detected on node `vpn-us-east-1`.",
    currentState: {
      hrStatus: "TERMINATED",
      vpnStatus: "ENABLED",
      activeSessions: 1,
      lastLogin: "2026-08-28 08:12 IST"
    },
    targetState: {
      hrStatus: "TERMINATED",
      vpnStatus: "DISABLED",
      activeSessions: 0,
      revokedAt: "Immediate"
    },
    requestedAt: "2026-08-28 10:15:00 IST",
    status: "PENDING"
  },
  {
    id: "APR-1091",
    repairId: "REP-8043",
    employeeName: "David Miller",
    employeeEmail: "david.miller@reconcileos.internal",
    department: "Finance & Operations",
    requestedAction: "Remove GitHub Organization Membership & Revoke SSH Keys",
    targetSystem: "GitHub Enterprise",
    riskLevel: "HIGH",
    reason: "HR record changed to TERMINATED. Account retains read/write access to 14 private repositories.",
    currentState: {
      hrStatus: "TERMINATED",
      githubStatus: "ACTIVE_MEMBER",
      sshKeys: 2,
      reposAccessCount: 14
    },
    targetState: {
      hrStatus: "TERMINATED",
      githubStatus: "REVOKED",
      sshKeys: 0,
      reposAccessCount: 0
    },
    requestedAt: "2026-08-28 09:31:00 IST",
    status: "PENDING"
  }
];

export const mockAuditLogs = [
  {
    id: "AUD-9901",
    timestamp: "2026-08-28 10:23:11 IST",
    eventType: "VERIFICATION_COMPLETED",
    actor: "ReconcileOS Daemon",
    target: "Rahul Kumar (rahul.kumar@reconcileos.internal)",
    system: "VPN",
    details: "Post-reconciliation verification check passed. System state confirmed DISABLED.",
    status: "SUCCESS"
  },
  {
    id: "AUD-9900",
    timestamp: "2026-08-28 10:22:04 IST",
    eventType: "RETRY_SUCCEEDED",
    actor: "ReconcileOS Daemon",
    target: "Rahul Kumar (rahul.kumar@reconcileos.internal)",
    system: "VPN",
    details: "Automatic retry #1 executed successfully. VPN status changed to DISABLED.",
    status: "SUCCESS"
  },
  {
    id: "AUD-9899",
    timestamp: "2026-08-28 10:20:45 IST",
    eventType: "EXECUTION_FAILED",
    actor: "ReconcileOS Daemon",
    target: "Rahul Kumar (rahul.kumar@reconcileos.internal)",
    system: "VPN",
    details: "Transient network timeout on RADIUS API endpoint `vpn-node-02`. Retrying in 60s.",
    status: "WARNING"
  },
  {
    id: "AUD-9898",
    timestamp: "2026-08-28 10:19:30 IST",
    eventType: "EXECUTION_STARTED",
    actor: "ReconcileOS Daemon",
    target: "Rahul Kumar (rahul.kumar@reconcileos.internal)",
    system: "VPN",
    details: "Initiated automated repair action `REVOKE_VPN_ACCESS` via VPN Connector API.",
    status: "INFO"
  },
  {
    id: "AUD-9897",
    timestamp: "2026-08-28 10:18:12 IST",
    eventType: "APPROVAL_GRANTED",
    actor: "secops-admin@reconcileos.internal",
    target: "Rahul Kumar (rahul.kumar@reconcileos.internal)",
    system: "Approvals",
    details: "Approval #APR-1092 granted by Human-in-the-Loop operator.",
    status: "SUCCESS"
  },
  {
    id: "AUD-9896",
    timestamp: "2026-08-28 10:15:00 IST",
    eventType: "APPROVAL_REQUESTED",
    actor: "ReconcileOS Rule Engine",
    target: "Rahul Kumar (rahul.kumar@reconcileos.internal)",
    system: "Approvals",
    details: "High-risk repair action queued for approval (Rule #INV-RULE-001).",
    status: "INFO"
  },
  {
    id: "AUD-9895",
    timestamp: "2026-08-28 10:14:05 IST",
    eventType: "REPAIR_PLAN_CREATED",
    actor: "ReconcileOS Workflow Engine",
    target: "Rahul Kumar (rahul.kumar@reconcileos.internal)",
    system: "Workflows",
    details: "Generated deterministic repair plan #REP-8042.",
    status: "INFO"
  },
  {
    id: "AUD-9894",
    timestamp: "2026-08-28 10:14:02 IST",
    eventType: "VIOLATION_DETECTED",
    actor: "ReconcileOS Scanner",
    target: "Rahul Kumar (rahul.kumar@reconcileos.internal)",
    system: "VPN",
    details: "Drift detected! HR status is TERMINATED but VPN access is ENABLED.",
    status: "CRITICAL"
  }
];
