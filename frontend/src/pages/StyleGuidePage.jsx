import React, { useState } from 'react';
import { StatCard } from '../components/ui/StatCard';
import { StatusPill } from '../components/ui/StatusPill';
import { Button } from '../components/ui/Button';
import { ActivityRow } from '../components/ui/ActivityRow';
import { ApprovalCard } from '../components/ui/ApprovalCard';
import { ChatBubble } from '../components/ui/ChatBubble';
import { StructuredRuleCard } from '../components/ui/StructuredRuleCard';
import { TimelineEntry } from '../components/ui/TimelineEntry';
import { mockEmployees, mockApprovals, mockRules, mockAuditLogs } from '../data/mockData';
import {
  Users,
  ShieldAlert,
  CheckCircle2,
  Activity,
  Plus,
  Trash2,
  RefreshCw,
  Filter
} from 'lucide-react';

export function StyleGuidePage() {
  const [toastMessage, setToastMessage] = useState(null);

  const handleAction = (label) => {
    setToastMessage(`Action triggered: "${label}"`);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const sampleEmployee = mockEmployees[0] || { fullName: "Alice Johnson", id: "e9f0d1a2-3b4c" };

  return (
    <div className="page-content">
      {/* Toast Banner */}
      {toastMessage && (
        <div
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            backgroundColor: 'var(--accent-primary)',
            color: '#FFFFFF',
            padding: '12px 20px',
            borderRadius: 'var(--radius-btn)',
            boxShadow: 'var(--shadow-floating)',
            zIndex: 1000,
            fontSize: '14px',
            fontWeight: 600
          }}
        >
          {toastMessage}
        </div>
      )}

      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span>Style Guide — Lavender Enterprise Admin</span>
          </h1>
          <p className="page-subtitle">
            Component primitives and design token specifications for ReconcileOS continuous identity reconciliation.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button variant="secondary" icon={RefreshCw} onClick={() => handleAction('Refresh tokens')}>
            Refresh Tokens
          </Button>
          <Button variant="primary" icon={Plus} onClick={() => handleAction('Add employee')}>
            Add Employee
          </Button>
        </div>
      </div>

      {/* Section 1: Stat Cards */}
      <section style={{ marginBottom: '36px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '14px', color: 'var(--text-primary)' }}>
          1. Stat Cards (Big Number + Label + Accent Bar)
        </h2>
        <div className="grid-4">
          <StatCard
            title="Total Employees"
            value={mockEmployees.length}
            status="healthy"
            statusLabel="4 Active, 2 Terminated"
            icon={Users}
          />
          <StatCard
            title="Active Violations"
            value="2"
            status="critical"
            statusLabel="1 Critical, 1 High"
            icon={ShieldAlert}
          />
          <StatCard
            title="Pending Approvals"
            value={mockApprovals.length}
            status="warning"
            statusLabel="Action required"
            icon={Activity}
          />
          <StatCard
            title="System Health"
            value="98.4%"
            status="healthy"
            statusLabel="Verified"
            icon={CheckCircle2}
            subtext="All 5 connectors operational"
          />
        </div>
      </section>

      {/* Section 2: Status Pills */}
      <section style={{ marginBottom: '36px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '14px', color: 'var(--text-primary)' }}>
          2. Status Pills (Dot + Text Label)
        </h2>
        <div className="card" style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px' }}>Critical Violation</div>
            <StatusPill status="critical" label="Critical Drift" />
          </div>
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px' }}>Warning / Drift</div>
            <StatusPill status="warning" label="Drift Detected" />
          </div>
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px' }}>Healthy / Verified</div>
            <StatusPill status="healthy" label="Healthy / Verified" />
          </div>
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px' }}>Inactive / Neutral</div>
            <StatusPill status="neutral" label="Terminated / Neutral" />
          </div>
        </div>
      </section>

      {/* Section 3: Buttons */}
      <section style={{ marginBottom: '36px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '14px', color: 'var(--text-primary)' }}>
          3. Button Variants & Focus States
        </h2>
        <div className="card" style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center' }}>
          <Button variant="primary" icon={Plus} onClick={() => handleAction('Add employee')}>
            Add employee
          </Button>
          <Button variant="secondary" icon={Filter} onClick={() => handleAction('Filter results')}>
            Filter records
          </Button>
          <Button variant="danger" icon={Trash2} onClick={() => handleAction('Terminate employee')}>
            Terminate employee
          </Button>
          <Button variant="ghost" onClick={() => handleAction('View details')}>
            View details
          </Button>
        </div>
      </section>

      {/* Grid for Activity Feed & Approval Card */}
      <div className="grid-2" style={{ marginBottom: '36px' }}>
        {/* Section 4: Activity Rows (Plain Divided Container) */}
        <div>
          <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '14px', color: 'var(--text-primary)' }}>
            4. Activity Feed (Plain Divided Rows)
          </h2>
          <div className="plain-divided-container">
            {mockAuditLogs.slice(0, 4).map((log) => (
              <ActivityRow
                key={log.id}
                icon={Activity}
                description={`${log.eventType}: ${log.target}`}
                timestamp={log.timestamp}
                status={log.status === 'CRITICAL' ? 'critical' : log.status === 'SUCCESS' ? 'healthy' : 'warning'}
                statusLabel={log.status}
              />
            ))}
          </div>
        </div>

        {/* Section 5: Approval Card */}
        <div>
          <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '14px', color: 'var(--text-primary)' }}>
            5. Approval Card (Card-per-item Intentional)
          </h2>
          {mockApprovals.slice(0, 1).map((appr) => (
            <ApprovalCard
              key={appr.id}
              id={appr.id}
              employeeName={appr.employeeName}
              employeeEmail={appr.employeeEmail}
              targetSystem={appr.targetSystem}
              requestedAction={appr.requestedAction}
              riskLevel={appr.riskLevel}
              reason={appr.reason}
              requestedAt={appr.requestedAt}
              onApprove={() => handleAction(`Approved ${appr.employeeName}`)}
              onReject={() => handleAction(`Rejected ${appr.employeeName}`)}
            />
          ))}
        </div>
      </div>

      {/* Grid for Chat Bubbles & Structured Rule Cards */}
      <div className="grid-2" style={{ marginBottom: '36px' }}>
        {/* Section 6: AI Assistant Chat Bubbles */}
        <div>
          <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '14px', color: 'var(--text-primary)' }}>
            6. AI Rule Assistant Chat Bubbles
          </h2>
          <div className="card">
            <ChatBubble
              sender="ai"
              message="I evaluated employee Rahul Kumar across connected connectors. HR status is TERMINATED, but VPN access is still ENABLED."
              timestamp="10:14:02 IST"
              actionTag="Invariant Violation Detected"
            />
            <ChatBubble
              sender="user"
              message="Generate a remediation plan to revoke VPN access immediately."
              timestamp="10:14:05 IST"
            />
            <ChatBubble
              sender="ai"
              message="Plan generated! Repair action REP-8042 requires SecOps approval before executing REST API revocation."
              timestamp="10:15:00 IST"
              actionTag="Approval Queued"
            />
          </div>
        </div>

        {/* Section 7: Structured Rule Card */}
        <div>
          <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '14px', color: 'var(--text-primary)' }}>
            7. Structured Rule Card (Condition → Consequence)
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <StructuredRuleCard
              ruleId={mockRules[0].id}
              title={mockRules[0].name}
              condition="HR.Status == 'TERMINATED'"
              consequence="VPN.Access = 'DISABLED'"
              severity={mockRules[0].severity}
              status={mockRules[0].status}
              targetSystems={mockRules[0].targetSystems}
            />
            <StructuredRuleCard
              ruleId={mockRules[1].id}
              title={mockRules[1].name}
              condition="HR.Status == 'TERMINATED'"
              consequence="GitHub.Membership = 'REVOKED'"
              severity={mockRules[1].severity}
              status={mockRules[1].status}
              targetSystems={mockRules[1].targetSystems}
            />
          </div>
        </div>
      </div>

      {/* Section 8: Timeline Entry */}
      <section style={{ marginBottom: '36px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '14px', color: 'var(--text-primary)' }}>
          8. Vertical Timeline Entries
        </h2>
        <div className="card">
          <TimelineEntry
            timestamp="10:14:02 IST"
            title="Drift Detected via Invariant Rule #INV-RULE-001"
            description={`Terminated status detected for ${sampleEmployee.fullName}. Downstream VPN access active.`}
            status="critical"
          />
          <TimelineEntry
            timestamp="10:14:05 IST"
            title="Remediation Plan Generated (#REP-8042)"
            description="Target Action: Revoke client certificates and disable RADIUS token."
            status="warning"
          />
          <TimelineEntry
            timestamp="10:18:12 IST"
            title="SecOps Human Approval Granted"
            description="Operator secops-admin@reconcileos.internal confirmed approval request."
            status="healthy"
          />
          <TimelineEntry
            timestamp="10:23:11 IST"
            title="Automated API Repair Verified"
            description="Post-reconciliation verification check passed. System state confirmed DISABLED."
            status="healthy"
            isLast={true}
          />
        </div>
      </section>
    </div>
  );
}
