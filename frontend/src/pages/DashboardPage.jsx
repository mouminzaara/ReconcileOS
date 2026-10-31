import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  RefreshCw,
  Play,
  ArrowRight,
  ShieldAlert,
  AlertTriangle,
  Activity,
  Users,
  CheckCircle2
} from 'lucide-react';
import { StatusPill } from '../components/ui/StatusPill';
import { Button } from '../components/ui/Button';
import { ActivityRow } from '../components/ui/ActivityRow';
import { StatCard } from '../components/ui/StatCard';
import { api } from '../services/api';

const INITIAL_STATS = {
  totalEmployees: '—',
  employeeStatus: 'neutral',
  employeeBreakdown: 'Loading directory...',
  activeViolations: '—',
  violationsStatus: 'neutral',
  violationsBreakdown: 'Checking drift...',
  pendingRepairs: '—',
  pendingStatus: 'neutral',
  pendingBreakdown: 'Checking approvals...',
  pendingSubtext: '',
  systemHealthValue: '—',
  systemHealthStatus: 'neutral',
  systemHealthLabel: 'Checking status...',
  systemHealthSubtext: 'Live telemetry unavailable',
  lastScanTimestamp: null
};

export function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [stats, setStats] = useState(INITIAL_STATS);
  const [violations, setViolations] = useState([]);
  const [systems, setSystems] = useState([]);
  const [activityLogs, setActivityLogs] = useState([]);
  const [lastScanTime, setLastScanTime] = useState(null);
  const [message, setMessage] = useState(null);
  const [dataError, setDataError] = useState(null);

  const loadDashboardData = async () => {
    setLoading(true);
    setDataError(null);
    try {
      const [empRes, vioRes, plansRes, stateRes, pendingRes, auditRes] = await Promise.allSettled([
        api.getEmployees(),
        api.getViolations(),
        api.getRepairPlans(),
        api.getCollectedStates(),
        api.getPendingApprovals(),
        api.getAuditLogs()
      ]);

      const failedApis = [];
      if (empRes.status === 'rejected') failedApis.push('Employees');
      if (vioRes.status === 'rejected') failedApis.push('Violations');
      if (plansRes.status === 'rejected') failedApis.push('Repair Plans');
      if (stateRes.status === 'rejected') failedApis.push('System State');
      if (pendingRes.status === 'rejected') failedApis.push('Approvals');
      if (auditRes.status === 'rejected') failedApis.push('Audit Logs');

      if (failedApis.length > 0) {
        setDataError(`Some data sources unavailable: ${failedApis.join(', ')}. Displayed values reflect only available data.`);
      }

      // 1. Process Employees
      let totalEmployees = '—';
      let employeeStatus = 'neutral';
      let employeeBreakdown = 'Directory unavailable';
      if (empRes.status === 'fulfilled') {
        const employeesList = empRes.value?.results || empRes.value;
        if (Array.isArray(employeesList)) {
          totalEmployees = typeof empRes.value?.count === 'number' ? empRes.value.count : employeesList.length;
          const activeCount = employeesList.filter(e => e.status === 'ACTIVE').length;
          const terminatedCount = employeesList.filter(e => e.status === 'TERMINATED').length;
          employeeStatus = 'healthy';
          employeeBreakdown = `${activeCount} Active, ${terminatedCount} Terminated`;
        }
      }

      // 2. Process Violations
      let activeViolationsCount = '—';
      let violationsStatus = 'neutral';
      let violationsBreakdown = 'Drift data unavailable';
      let formattedViolations = [];
      const rawViolations = vioRes.status === 'fulfilled' ? (vioRes.value?.results || vioRes.value) : null;
      if (Array.isArray(rawViolations)) {
        const openViolations = rawViolations.filter(v => v.status === 'OPEN');
        activeViolationsCount = openViolations.length;
        if (activeViolationsCount > 0) {
          const criticalCount = openViolations.filter(v => v.severity === 'CRITICAL').length;
          const highCount = openViolations.filter(v => v.severity === 'HIGH').length;
          const otherCount = activeViolationsCount - criticalCount - highCount;
          violationsStatus = 'critical';
          violationsBreakdown = otherCount > 0
            ? `${criticalCount} Critical, ${highCount} High, ${otherCount} Other`
            : `${criticalCount} Critical, ${highCount} High`;
        } else {
          violationsStatus = 'healthy';
          violationsBreakdown = 'Zero drift across systems';
        }

        formattedViolations = rawViolations.map(v => ({
          id: v.id ? `VIO-${v.id.substring(0, 8).toUpperCase()}` : v.rule_code,
          fullId: v.id,
          employeeName: v.employee_name || (v.employee && v.employee.full_name) || 'Unknown',
          employeeEmail: v.employee_email || (v.employee && v.employee.email) || '',
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
      }
      setViolations(formattedViolations);

      // 3. Process Pending Approvals
      let pendingCount = '—';
      let pendingStatus = 'neutral';
      let pendingBreakdown = 'Approvals unavailable';
      let pendingSubtext = '';
      if (pendingRes.status === 'fulfilled') {
        const val = pendingRes.value;
        const pendingList = val?.results || val;
        const count = typeof val?.count === 'number'
          ? val.count
          : (Array.isArray(pendingList) ? pendingList.length : 0);
        pendingCount = count;
        if (count > 0) {
          pendingStatus = 'warning';
          pendingBreakdown = 'Action required';
          pendingSubtext = `${count} awaiting SecOps approval`;
        } else {
          pendingStatus = 'healthy';
          pendingBreakdown = 'Queue clear';
          pendingSubtext = 'All repair plans clear';
        }
      }

      // 4. Process Audit Logs
      if (auditRes.status === 'fulfilled') {
        const rawAuditLogs = auditRes.value?.results || auditRes.value;
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
      } else {
        setActivityLogs([]);
      }

      // 5. Process Systems & Health (No fabricated latency or health percentages)
      let systemHealthValue = 'Unavailable';
      let systemHealthStatus = 'neutral';
      let systemHealthLabel = 'Health status unavailable';
      let systemHealthSubtext = 'Live telemetry unmeasured';
      let configuredSystems = [];

      if (stateRes.status === 'fulfilled') {
        const collectedStates = stateRes.value?.results || stateRes.value;
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

          if (Array.isArray(rawViolations)) {
            rawViolations.filter(v => v.status === 'OPEN').forEach(v => {
              const key = (v.affected_system || '').toUpperCase();
              if (activeSystemsMap[key]) {
                activeSystemsMap[key].hasDrift = true;
              }
            });
          }

          const nowStr = new Date().toLocaleTimeString();
          configuredSystems = [
            { id: 'sys-1', name: 'BambooHR Gateway', type: 'HR System of Record', protocol: 'REST / OAuth2', status: 'HEALTHY', activeAccounts: activeSystemsMap.HR.active, lastChecked: nowStr },
            { id: 'sys-2', name: 'OpenVPN Gateway', type: 'Network Access Control', protocol: 'OpenVPN Management API', status: activeSystemsMap.VPN.hasDrift ? 'DRIFT_DETECTED' : 'HEALTHY', activeAccounts: activeSystemsMap.VPN.active, lastChecked: nowStr },
            { id: 'sys-3', name: 'GitHub Enterprise', type: 'Source Code & Organization', protocol: 'GitHub REST v3 / GraphQL', status: activeSystemsMap.GitHub.hasDrift ? 'DRIFT_DETECTED' : 'HEALTHY', activeAccounts: activeSystemsMap.GitHub.active, lastChecked: nowStr },
            { id: 'sys-4', name: 'AWS Cloud IAM', type: 'Cloud Infrastructure & Roles', protocol: 'AWS Security Token Service', status: activeSystemsMap.Cloud.hasDrift ? 'DRIFT_DETECTED' : 'HEALTHY', activeAccounts: activeSystemsMap.Cloud.active, lastChecked: nowStr },
            { id: 'sys-5', name: 'Slack Workspace', type: 'Corporate Chat & Provisioning', protocol: 'Slack SCIM API v2', status: activeSystemsMap.Slack.hasDrift ? 'DRIFT_DETECTED' : 'HEALTHY', activeAccounts: activeSystemsMap.Slack.active, lastChecked: nowStr }
          ];

          systemHealthValue = `${configuredSystems.length} Configured`;
          systemHealthStatus = activeViolationsCount > 0 ? 'warning' : 'neutral';
          systemHealthLabel = 'Health status unavailable';
          systemHealthSubtext = 'Live telemetry unmeasured';
        } else {
          systemHealthValue = '0 Configured';
          systemHealthStatus = 'neutral';
          systemHealthLabel = 'No collected states';
          systemHealthSubtext = 'Run reconciliation scan';
        }
      } else {
        systemHealthValue = 'Unavailable';
        systemHealthStatus = 'warning';
        systemHealthLabel = 'Health status unavailable';
        systemHealthSubtext = 'System state API failed';
      }
      setSystems(configuredSystems);

      setStats({
        totalEmployees,
        employeeStatus,
        employeeBreakdown,
        activeViolations: activeViolationsCount,
        violationsStatus,
        violationsBreakdown,
        pendingRepairs: pendingCount,
        pendingStatus,
        pendingBreakdown,
        pendingSubtext,
        systemHealthValue,
        systemHealthStatus,
        systemHealthLabel,
        systemHealthSubtext,
        lastScanTimestamp: new Date().toLocaleTimeString()
      });

      setLastScanTime(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Dashboard data load failed:', err);
      setDataError('Failed to connect to backend API. Dashboard shows no live data.');
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
      const res = await api.runContinuousMonitor(false);
      const violationsCount = res.violations_detected_count || 0;
      const plansCount = res.repair_plans_generated_count || 0;

      if (violationsCount > 0) {
        setMessage({
          type: 'warning',
          text: `Continuous Integrity Monitor completed: ${violationsCount} drift violation(s) detected. ${plansCount} repair plan(s) generated and awaiting review in Approvals Queue.`
        });
      } else {
        setMessage({
          type: 'success',
          text: `Continuous Integrity Monitor completed: System verified consistent (0 drift violations detected).`
        });
      }
      await loadDashboardData();
    } catch (err) {
      setMessage({ type: 'error', text: `Monitoring error: ${err.message}` });
    } finally {
      setActionLoading(false);
    }
  };

  const activeViolation = violations.find(v => (v.status === 'OPEN' || v.status === 'ACTIVE') && v.severity === 'CRITICAL') || violations.find(v => v.status === 'OPEN' || v.status === 'ACTIVE');

  return (
    <div className="page-content">
      {/* Editorial Header */}
      <div className="page-header">
        <div>
          <div className="page-eyebrow">
            <span className="page-eyebrow-dot" />
            <span>Continuous Identity Integrity</span>
          </div>
          <h1 className="page-title">Operations Workspace</h1>
          <p className="page-subtitle">
            Continuous authorization drift detection, cross-system reconciliation, and deterministic self-healing
          </p>
        </div>

        <div className="page-header-actions">
          {lastScanTime && (
            <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginRight: '8px' }} className="font-mono">
              Synced: {lastScanTime}
            </span>
          )}
          <Button variant="secondary" icon={RefreshCw} onClick={handleRunReconciliation} disabled={actionLoading}>
            Audit Drift
          </Button>
          <Button variant="primary" icon={Play} onClick={handleRunContinuousMonitor} disabled={actionLoading}>
            Run Self-Healing
          </Button>
        </div>
      </div>

      {/* Data Availability Warning */}
      {dataError && (
        <div
          style={{
            marginBottom: 'var(--space-xl)',
            padding: '12px 18px',
            borderRadius: '10px',
            backgroundColor: 'var(--status-warning-bg)',
            border: '1px solid var(--status-warning-border)',
            color: 'var(--status-warning)',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          <AlertTriangle size={16} />
          <span>{dataError}</span>
        </div>
      )}

      {/* Feedback Banner */}
      {message && (
        <div
          style={{
            marginBottom: 'var(--space-xl)',
            padding: '14px 20px',
            borderRadius: '10px',
            backgroundColor: message.type === 'success'
              ? 'var(--status-healthy-bg)'
              : message.type === 'warning'
                ? 'var(--status-warning-bg)'
                : 'var(--status-critical-bg)',
            border: `1px solid ${message.type === 'success'
              ? 'var(--status-healthy-border)'
              : message.type === 'warning'
                ? 'var(--status-warning-border)'
                : 'var(--status-critical-border)'}`,
            color: message.type === 'success'
              ? 'var(--status-healthy)'
              : message.type === 'warning'
                ? 'var(--status-warning)'
                : 'var(--status-critical)',
            fontSize: '13.5px',
            lineHeight: 1.5
          }}
        >
          {message.text}
        </div>
      )}

      {/* Stat Cards Grid (Lavender Enterprise Admin) */}
      <div className="grid-4">
        <StatCard
          title="Total Employees"
          value={stats.totalEmployees}
          status={stats.employeeStatus}
          statusLabel={stats.employeeBreakdown}
          icon={Users}
        />

        <StatCard
          title="Active Violations"
          value={stats.activeViolations}
          status={stats.violationsStatus}
          statusLabel={stats.violationsBreakdown}
          icon={ShieldAlert}
        />

        <StatCard
          title="Pending Approvals"
          value={stats.pendingRepairs}
          status={stats.pendingStatus}
          statusLabel={stats.pendingBreakdown}
          subtext={stats.pendingSubtext}
          icon={Activity}
        />

        <StatCard
          title="System Health"
          value={stats.systemHealthValue}
          status={stats.systemHealthStatus}
          statusLabel={stats.systemHealthLabel}
          subtext={stats.systemHealthSubtext}
          icon={CheckCircle2}
        />
      </div>

      {/* Priority Focus: Drift Anomaly Callout (Editorial narrative block) */}
      {activeViolation && (
        <div
          style={{
            marginBottom: 'var(--space-2xl)',
            padding: '28px 32px',
            borderRadius: 'var(--radius-card)',
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-hairline)',
            boxShadow: 'var(--shadow-card)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '24px'
          }}
        >
          <div style={{ maxWidth: '680px' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '11px', fontWeight: 600, color: 'var(--status-critical)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '8px' }}>
              <ShieldAlert size={14} />
              <span>Priority Drift Anomaly Detected</span>
            </div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px', letterSpacing: '-0.02em' }}>
              {activeViolation.employeeName} retains active {activeViolation.systemKey} credentials
            </h3>
            <p style={{ fontSize: '13.5px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              HR lifecycle status is <strong>{activeViolation.hrStatus}</strong>, but downstream {activeViolation.systemKey} access remains <strong>{activeViolation.actualState}</strong>.
              Remediation plan generated — SecOps approval required prior to credential revocation.
            </p>
          </div>

          <Link to="/approvals" style={{ flexShrink: 0 }}>
            <Button variant="primary" icon={ArrowRight}>
              Review in Approvals
            </Button>
          </Link>
        </div>
      )}

      {/* Two-Column Editorial Sections: Connected Gateways & Activity Stream */}
      <div className="grid-2">
        {/* Connected System Gateways */}
        <div>
          <div className="section-header">
            <div>
              <h2 className="section-title">Connected Gateways</h2>
              <p className="section-desc">Target system connectors and drift tracking across services</p>
            </div>
            <Link to="/systems" style={{ fontSize: '13px', fontWeight: 600 }}>
              All systems →
            </Link>
          </div>

          <div className="editorial-table-container">
            {systems.length > 0 ? (
              <table className="editorial-table">
                <thead>
                  <tr>
                    <th>Gateway</th>
                    <th>Drift Status</th>
                    <th>Telemetry</th>
                  </tr>
                </thead>
                <tbody>
                  {systems.map((sys) => {
                    const isDrift = sys.status === 'DRIFT_DETECTED';
                    return (
                      <tr key={sys.id}>
                        <td>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{sys.name}</div>
                          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>{sys.type}</div>
                        </td>
                        <td>
                          <StatusPill status={isDrift ? 'warning' : 'healthy'} label={isDrift ? 'Drift' : 'In Sync'} size="small" />
                        </td>
                        <td>
                          <div style={{ fontSize: '12.5px', color: 'var(--text-primary)', fontWeight: 500 }}>
                            {sys.activeAccounts} {sys.activeAccounts === 1 ? 'account' : 'accounts'}
                          </div>
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                            Latency unmeasured
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <div style={{ padding: '40px 24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                {loading ? 'Loading gateway data...' : 'System state unavailable. Run a reconciliation scan.'}
              </div>
            )}
          </div>
        </div>

        {/* Continuous Audit Stream */}
        <div>
          <div className="section-header">
            <div>
              <h2 className="section-title">Continuous Audit Stream</h2>
              <p className="section-desc">Cryptographically chained records of integrity events</p>
            </div>
            <Link to="/audit-logs" style={{ fontSize: '13px', fontWeight: 600 }}>
              Full log →
            </Link>
          </div>

          <div className="plain-divided-container">
            {loading ? (
              <div style={{ padding: '40px 24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                Loading audit stream...
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
              <div style={{ padding: '40px 24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                No recent activity records found.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
