import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  AlertTriangle,
  Wrench,
  Server,
  RefreshCw,
  Play,
  ArrowRight,
  Activity,
  ShieldAlert
} from 'lucide-react';
import { StatCard } from '../components/ui/StatCard';
import { StatusPill } from '../components/ui/StatusPill';
import { Button } from '../components/ui/Button';
import { ActivityRow } from '../components/ui/ActivityRow';
import { api } from '../services/api';
import {
  mockStats,
  mockConnectedSystems,
  mockViolations
} from '../data/mockData';

export function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [stats, setStats] = useState(mockStats);
  const [violations, setViolations] = useState(mockViolations);
  const [systems, setSystems] = useState(mockConnectedSystems);
  const [activityLogs, setActivityLogs] = useState([]);
  const [lastScanTime, setLastScanTime] = useState('Just now');
  const [message, setMessage] = useState(null);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [empRes, vioRes, plansRes, stateRes, pendingRes, auditRes] = await Promise.allSettled([
        api.getEmployees(),
        api.getViolations(),
        api.getRepairPlans(),
        api.getCollectedStates(),
        api.getPendingApprovals(),
        api.getAuditLogs()
      ]);

      const employeesList = empRes.status === 'fulfilled' ? (empRes.value.results || empRes.value) : [];
      const violationsList = vioRes.status === 'fulfilled' ? (vioRes.value.results || vioRes.value) : [];
      const plansList = plansRes.status === 'fulfilled' ? (plansRes.value.results || plansRes.value) : [];
      const pendingList = pendingRes.status === 'fulfilled' ? (pendingRes.value.results || pendingRes.value) : [];
      const rawAuditLogs = auditRes.status === 'fulfilled' ? (auditRes.value.results || auditRes.value) : [];
      const collectedStates = stateRes.status === 'fulfilled' ? (stateRes.value.results || stateRes.value) : [];

      if (Array.isArray(violationsList) && violationsList.length > 0) {
        const formattedViolations = violationsList.map(v => ({
          id: v.id ? `VIO-${v.id.substring(0, 8).toUpperCase()}` : v.rule_code,
          fullId: v.id,
          employeeName: v.employee_name || (v.employee && v.employee.full_name) || 'Rahul Kumar',
          employeeEmail: v.employee_email || (v.employee && v.employee.email) || 'rahul.kumar@reconcileos.internal',
          hrStatus: v.employee_status || 'TERMINATED',
          systemKey: v.affected_system || 'VPN',
          ruleId: v.rule_code || 'INV-RULE-001',
          ruleName: v.rule_name || 'Invariant Rule',
          expectedState: v.expected_state || 'DISABLED',
          actualState: v.actual_state || 'ENABLED',
          severity: v.severity || 'CRITICAL',
          status: v.status || 'OPEN',
          detectedAt: v.detected_at ? new Date(v.detected_at).toLocaleString() : 'Just now'
        }));
        setViolations(formattedViolations);
      }

      if (Array.isArray(rawAuditLogs) && rawAuditLogs.length > 0) {
        const formattedLogs = rawAuditLogs.slice(0, 5).map(log => ({
          id: log.id ? `AUD-${String(log.id).substring(0, 8).toUpperCase()}` : (log.correlation_id || 'AUD-0000'),
          eventType: log.event_type || 'EVENT',
          target: log.employee_name || log.employee_email || log.action || 'Directory Resource',
          timestamp: log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : 'Just now',
          status: log.result || 'SUCCESS'
        }));
        setActivityLogs(formattedLogs);
      } else {
        setActivityLogs([]);
      }

      if (Array.isArray(collectedStates) && collectedStates.length > 0) {
        const activeSystemsMap = {
          HR: { active: collectedStates.length, hasDrift: false },
          VPN: { active: 0, hasDrift: false },
          GitHub: { active: 0, hasDrift: false },
          Cloud: { active: 0, hasDrift: false },
          Slack: { active: 0, hasDrift: false }
        };

        collectedStates.forEach(st => {
          const sys = st.systems || {};
          if (sys.vpn?.access_status === 'ENABLED') activeSystemsMap.VPN.active += 1;
          if (sys.github?.access_status === 'ACTIVE' || sys.github?.access_status === 'MEMBER') activeSystemsMap.GitHub.active += 1;
          if (sys.cloud?.access_status && sys.cloud?.access_status !== 'NO_ROLE' && sys.cloud?.access_status !== 'NOT_PROVISIONED') activeSystemsMap.Cloud.active += 1;
          if (sys.slack?.access_status === 'ACTIVE') activeSystemsMap.Slack.active += 1;
        });

        violationsList.filter(v => v.status === 'OPEN').forEach(v => {
          const key = (v.affected_system || '').toUpperCase();
          if (activeSystemsMap[key]) {
            activeSystemsMap[key].hasDrift = true;
          }
        });

        const nowStr = new Date().toLocaleTimeString();
        setSystems([
          { id: 'sys-1', name: 'BambooHR Gateway', type: 'HR System of Record', protocol: 'REST / OAuth2', status: 'HEALTHY', activeAccounts: activeSystemsMap.HR.active, latency: '12ms', lastChecked: nowStr },
          { id: 'sys-2', name: 'OpenVPN Gateway', type: 'Network Access Control', protocol: 'OpenVPN Management API', status: activeSystemsMap.VPN.hasDrift ? 'DRIFT_DETECTED' : 'HEALTHY', activeAccounts: activeSystemsMap.VPN.active, latency: '45ms', lastChecked: nowStr },
          { id: 'sys-3', name: 'GitHub Enterprise', type: 'Source Code & Organization', protocol: 'GitHub REST v3 / GraphQL', status: activeSystemsMap.GitHub.hasDrift ? 'DRIFT_DETECTED' : 'HEALTHY', activeAccounts: activeSystemsMap.GitHub.active, latency: '88ms', lastChecked: nowStr },
          { id: 'sys-4', name: 'AWS Cloud IAM', type: 'Cloud Infrastructure & Roles', protocol: 'AWS Security Token Service', status: activeSystemsMap.Cloud.hasDrift ? 'DRIFT_DETECTED' : 'HEALTHY', activeAccounts: activeSystemsMap.Cloud.active, latency: '120ms', lastChecked: nowStr },
          { id: 'sys-5', name: 'Slack Workspace', type: 'Corporate Chat & Provisioning', protocol: 'Slack SCIM API v2', status: activeSystemsMap.Slack.hasDrift ? 'DRIFT_DETECTED' : 'HEALTHY', activeAccounts: activeSystemsMap.Slack.active, latency: '34ms', lastChecked: nowStr }
        ]);
      }

      const activeViolationsCount = Array.isArray(violationsList) ? violationsList.filter(v => v.status === 'OPEN').length : 0;
      const completedPlansCount = Array.isArray(plansList) ? plansList.filter(p => p.status === 'COMPLETED' || p.status === 'SUCCESS').length : 0;

      setStats({
        totalEmployees: Array.isArray(employeesList) ? employeesList.length : mockStats.totalEmployees,
        activeViolations: activeViolationsCount,
        pendingRepairs: Array.isArray(pendingList) ? pendingList.length : mockStats.pendingRepairs,
        successfulReconciliations: completedPlansCount,
        systemHealthPercent: activeViolationsCount === 0 ? 100 : Math.max(60, 100 - activeViolationsCount * 10),
        lastScanTimestamp: new Date().toLocaleTimeString()
      });

      setLastScanTime(new Date().toLocaleTimeString());
    } catch (err) {
      console.warn('Backend API connection failed, using fallback metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleRunReconciliation = async () => {
    setActionLoading(true);
    setMessage(null);
    try {
      const res = await api.runReconciliation();
      setMessage({ type: 'success', text: res.message || 'Reconciliation audit completed successfully.' });
      await loadDashboardData();
    } catch (err) {
      setMessage({ type: 'error', text: `Reconciliation audit error: ${err.message}` });
    } finally {
      setActionLoading(false);
    }
  };

  const handleRunContinuousMonitor = async () => {
    setActionLoading(true);
    setMessage(null);
    try {
      const res = await api.runContinuousMonitor(true);
      setMessage({
        type: 'success',
        text: `Continuous Integrity Monitor cycle completed. Status: ${res.system_status || 'HEALTHY'}, Repairs: ${res.repairs_executed_count || 0}`
      });
      await loadDashboardData();
    } catch (err) {
      setMessage({ type: 'error', text: `Monitoring error: ${err.message}` });
    } finally {
      setActionLoading(false);
    }
  };

  const activeViolation = violations.find(v => v.severity === 'CRITICAL' || v.status === 'ACTIVE' || v.status === 'OPEN') || violations[0];

  return (
    <div className="page-content">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span>ReconcileOS Dashboard</span>
          </h1>
          <p className="page-subtitle">
            Continuous authorization drift detection and automated self-healing
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginRight: '4px' }} className="font-mono">
            Last scan: {lastScanTime}
          </span>
          <Button variant="secondary" icon={RefreshCw} onClick={handleRunReconciliation} disabled={actionLoading}>
            Audit Drift
          </Button>
          <Button variant="primary" icon={Play} onClick={handleRunContinuousMonitor} disabled={actionLoading}>
            Run Self-Healing
          </Button>
        </div>
      </div>

      {/* Feedback Banner */}
      {message && (
        <div
          style={{
            marginBottom: '20px',
            padding: '12px 16px',
            borderRadius: 'var(--radius-btn)',
            backgroundColor: message.type === 'success' ? 'var(--status-healthy-bg)' : 'var(--status-critical-bg)',
            border: `1px solid ${message.type === 'success' ? 'var(--status-healthy-border)' : 'var(--status-critical-border)'}`,
            color: message.type === 'success' ? 'var(--status-healthy)' : 'var(--status-critical)',
            fontSize: '13px',
            fontWeight: 600
          }}
        >
          {message.text}
        </div>
      )}

      {/* Restrained Summary Metrics */}
      <div className="grid-4">
        <StatCard
          title="Active Violations"
          value={stats.activeViolations}
          status="critical"
          statusLabel="Drift Detected"
          icon={AlertTriangle}
        />
        <StatCard
          title="Pending Approvals"
          value={stats.pendingRepairs}
          status="warning"
          statusLabel="Action Required"
          icon={Wrench}
        />
        <StatCard
          title="Systems Healthy"
          value={`${systems.filter(s => s.status === 'HEALTHY').length} / ${systems.length}`}
          status="healthy"
          statusLabel="Verified"
          icon={Server}
        />
        <StatCard
          title="Monitored Employees"
          value={stats.totalEmployees}
          status="neutral"
          statusLabel="HR Directory"
          icon={Users}
        />
      </div>

      {/* Attention Required Panel */}
      {activeViolation && (
        <div
          style={{
            marginBottom: '24px',
            padding: '16px 20px',
            borderRadius: 'var(--radius-card)',
            backgroundColor: 'var(--status-critical-bg)',
            border: '1px solid var(--status-critical-border)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: 'var(--radius-btn)',
                backgroundColor: 'var(--status-critical)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#FFFFFF'
              }}
            >
              <ShieldAlert size={18} />
            </div>
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--status-critical)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Attention Required — Critical Authorization Drift
              </div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
                {activeViolation.employeeName} ({activeViolation.employeeEmail}) HR status is <strong>{activeViolation.hrStatus}</strong>, but <strong>{activeViolation.systemKey}</strong> access remains <strong>{activeViolation.actualState}</strong>.
              </div>
            </div>
          </div>

          <Link to="/approvals">
            <Button variant="danger" size="small" icon={ArrowRight}>
              Review Repair Action
            </Button>
          </Link>
        </div>
      )}

      {/* Grid: System Health Table + Recent Activity */}
      <div className="grid-2" style={{ marginBottom: '24px' }}>
        {/* System Health List */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>System Connectors</h2>
            <Link to="/systems" style={{ fontSize: '12px', color: 'var(--accent-primary)', fontWeight: 600 }}>
              View Connectors →
            </Link>
          </div>

          <div className="plain-divided-container">
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-base)', borderBottom: '1px solid var(--border-hairline)' }}>
                  <th style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>System</th>
                  <th style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>Status</th>
                  <th style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>Last Checked</th>
                </tr>
              </thead>
              <tbody>
                {systems.map((sys) => {
                  const isDrift = sys.status === 'DRIFT_DETECTED';
                  return (
                    <tr key={sys.id} style={{ borderBottom: '1px solid var(--border-hairline)' }}>
                      <td style={{ padding: '12px 14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {sys.name}
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 400 }}>{sys.type}</div>
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <StatusPill status={isDrift ? 'warning' : 'healthy'} label={isDrift ? 'Drift Detected' : 'Healthy'} size="small" />
                      </td>
                      <td className="font-mono" style={{ padding: '12px 14px', fontSize: '12px', color: 'var(--text-muted)' }}>
                        {sys.lastChecked}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Activity Log Feed */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>Recent Activity</h2>
            <Link to="/audit-logs" style={{ fontSize: '12px', color: 'var(--accent-primary)', fontWeight: 600 }}>
              View Audit Logs →
            </Link>
          </div>

          <div className="plain-divided-container">
            {loading ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                Loading recent activity...
              </div>
            ) : activityLogs.length > 0 ? (
              activityLogs.map((log) => (
                <ActivityRow
                  key={log.id}
                  icon={Activity}
                  description={`${log.eventType}: ${log.target}`}
                  timestamp={log.timestamp}
                  status={log.status === 'CRITICAL' || log.status === 'FAILURE' ? 'critical' : log.status === 'SUCCESS' ? 'healthy' : 'warning'}
                  statusLabel={log.status}
                />
              ))
            ) : (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                No recent activity records found.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

