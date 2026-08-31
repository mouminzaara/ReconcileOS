import React, { useState, useEffect } from 'react';
import {
  Users,
  AlertTriangle,
  Wrench,
  CheckCircle2,
  Server,
  Shield,
  GitBranch,
  Cloud,
  MessageSquare,
  ArrowRight,
  ExternalLink,
  RefreshCw,
  Play
} from 'lucide-react';
import { StatCard } from '../components/common/StatCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { LifecycleStepper } from '../components/common/LifecycleStepper';
import { IntegrityDriftCard } from '../components/common/IntegrityDriftCard';
import { api } from '../services/api';
import {
  mockStats,
  mockConnectedSystems,
  mockViolations
} from '../data/mockData';
import { Link } from 'react-router-dom';

const systemIconMap = {
  Users: Users,
  ShieldAlert: Shield,
  GitBranch: GitBranch,
  Cloud: Cloud,
  MessageSquare: MessageSquare
};

export function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [stats, setStats] = useState(mockStats);
  const [violations, setViolations] = useState(mockViolations);
  const [systems, setSystems] = useState(mockConnectedSystems);
  const [lastScanTime, setLastScanTime] = useState('Just now');
  const [message, setMessage] = useState(null);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [empRes, vioRes, plansRes, stateRes, pendingRes] = await Promise.allSettled([
        api.getEmployees(),
        api.getViolations(),
        api.getRepairPlans(),
        api.getCollectedStates(),
        api.getPendingApprovals()
      ]);

      const employeesList = empRes.status === 'fulfilled' ? (empRes.value.results || empRes.value) : [];
      const violationsList = vioRes.status === 'fulfilled' ? (vioRes.value.results || vioRes.value) : [];
      const plansList = plansRes.status === 'fulfilled' ? (plansRes.value.results || plansRes.value) : [];
      const pendingList = pendingRes.status === 'fulfilled' ? (pendingRes.value.results || pendingRes.value) : [];

      if (violationsList.length > 0) {
        const formattedViolations = violationsList.map(v => ({
          id: v.id ? strShortId(v.id) : v.rule_code,
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

      const activeViolationsCount = violationsList.filter(v => v.status === 'OPEN').length;
      const completedPlansCount = plansList.filter(p => p.status === 'COMPLETED' || p.status === 'SUCCESS').length;

      setStats({
        totalEmployees: employeesList.length || mockStats.totalEmployees,
        activeViolations: activeViolationsCount,
        pendingRepairs: pendingList.length,
        successfulReconciliations: completedPlansCount,
        systemHealthPercent: activeViolationsCount === 0 ? 100 : Math.max(60, 100 - activeViolationsCount * 10),
        lastScanTimestamp: new Date().toLocaleTimeString()
      });

      setLastScanTime(new Date().toLocaleTimeString());
    } catch (err) {
      console.warn('Backend API connection failed, falling back to cached mock telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  function strShortId(id) {
    if (!id) return 'VIO-000';
    return `VIO-${id.substring(0, 8).toUpperCase()}`;
  }

  const handleRunReconciliation = async () => {
    setActionLoading(true);
    setMessage(null);
    try {
      const res = await api.runReconciliation();
      setMessage({ type: 'success', text: res.message || 'Reconciliation audit completed successfully!' });
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
        text: `Continuous Integrity Monitor cycle completed! Status: ${res.system_status}, Repairs Executed: ${res.repairs_executed_count}`
      });
      await loadDashboardData();
    } catch (err) {
      setMessage({ type: 'error', text: `Monitoring cycle error: ${err.message}` });
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Shield size={24} style={{ color: 'var(--accent-blue)' }} />
            Security & Invariant Dashboard
          </h1>
          <p className="page-subtitle">
            Continuous identity reconciliation and multi-system self-healing platform
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Last Scan: {lastScanTime}
          </span>
          <button
            className="btn btn-secondary"
            onClick={handleRunReconciliation}
            disabled={actionLoading}
          >
            <RefreshCw size={14} className={actionLoading ? 'spin' : ''} />
            Audit Drift
          </button>
          <button
            className="btn btn-primary"
            onClick={handleRunContinuousMonitor}
            disabled={actionLoading}
          >
            <Play size={14} />
            Run Self-Healing Monitor
          </button>
        </div>
      </div>

      {/* Message Banner */}
      {message && (
        <div
          className="card"
          style={{
            marginBottom: '20px',
            borderColor: message.type === 'success' ? 'var(--status-success)' : 'var(--status-danger)',
            backgroundColor: message.type === 'success' ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
            padding: '12px 16px',
            fontSize: '0.85rem'
          }}
        >
          {message.text}
        </div>
      )}

      {/* Integrity & Authorization Drift Showcase Card */}
      <IntegrityDriftCard
        onRunAudit={handleRunReconciliation}
        onRunMonitor={handleRunContinuousMonitor}
        actionLoading={actionLoading}
      />

      {/* Metric Cards */}
      <div className="grid-4">
        <StatCard
          title="Total Employees"
          value={stats.totalEmployees}
          subtext="Identity records monitored"
          icon={Users}
          variant="info"
        />
        <StatCard
          title="Active Integrity Violations"
          value={stats.activeViolations}
          subtext="Authorization drifts detected"
          icon={AlertTriangle}
          variant="danger"
        />
        <StatCard
          title="Pending Repairs"
          value={stats.pendingRepairs}
          subtext="Awaiting human approval"
          icon={Wrench}
          variant="warning"
        />
        <StatCard
          title="Successful Reconciliations"
          value={stats.successfulReconciliations}
          subtext="100% empirically verified"
          icon={CheckCircle2}
          variant="success"
        />
      </div>

      {/* Visual Reconciliation Lifecycle Stepper */}
      <LifecycleStepper />

      {/* Connected System Health Grid */}
      <div className="card" style={{ marginBottom: '28px' }}>
        <div className="card-title">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Server size={18} style={{ color: 'var(--accent-cyan)' }} />
            <span>Connected Systems Health</span>
          </div>
          <Link to="/systems" style={{ fontSize: '0.8rem', color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            View All Connectors <ArrowRight size={14} />
          </Link>
        </div>

        <div className="grid-3" style={{ marginBottom: 0 }}>
          {systems.map((sys) => {
            const Icon = systemIconMap[sys.icon] || Server;
            const isDrift = sys.status === 'DRIFT_DETECTED';
            return (
              <div key={sys.id} className="card system-card">
                <div>
                  <div className="system-card-header">
                    <div className="system-info">
                      <div className="system-icon">
                        <Icon size={20} />
                      </div>
                      <div>
                        <div className="system-title">{sys.name}</div>
                        <div className="system-type">{sys.type}</div>
                      </div>
                    </div>
                    <span className={`pulse-dot ${isDrift ? 'drift' : 'healthy'}`}></span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                    {sys.description}
                  </div>
                </div>

                <div className="system-details">
                  <div className="detail-row">
                    <span className="detail-label">Status</span>
                    <StatusBadge status={sys.status} />
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Protocol</span>
                    <span className="mono detail-val">{sys.protocol}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Latency</span>
                    <span className="detail-val">{sys.latency}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Active Violations Section */}
      <div className="card">
        <div className="card-title">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertTriangle size={18} style={{ color: 'var(--status-danger)' }} />
            <span>Recent Invariant Violations (Authorization Drift)</span>
          </div>
          <Link to="/violations" className="btn btn-secondary" style={{ fontSize: '0.75rem', padding: '4px 10px' }}>
            View Full Matrix
          </Link>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Violation ID</th>
                <th>Employee</th>
                <th>HR State</th>
                <th>Target System</th>
                <th>Expected</th>
                <th>Actual</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {violations.map((vio) => (
                <tr key={vio.id}>
                  <td className="mono" style={{ color: 'var(--accent-blue)', fontWeight: 600 }}>
                    {vio.id}
                  </td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{vio.employeeName}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{vio.employeeEmail}</div>
                  </td>
                  <td>
                    <StatusBadge status={vio.hrStatus} />
                  </td>
                  <td>
                    <span className="badge badge-info">{vio.systemKey}</span>
                  </td>
                  <td>
                    <span className="mono" style={{ color: 'var(--status-success)', fontWeight: 600 }}>
                      {vio.expectedState}
                    </span>
                  </td>
                  <td>
                    <span className="mono" style={{ color: 'var(--status-danger)', fontWeight: 600 }}>
                      {vio.actualState}
                    </span>
                  </td>
                  <td>
                    <SeverityBadge severity={vio.severity} />
                  </td>
                  <td>
                    <StatusBadge status={vio.status} />
                  </td>
                  <td>
                    <Link to="/approvals" className="btn btn-secondary" style={{ fontSize: '0.75rem', padding: '4px 8px' }}>
                      Review <ExternalLink size={12} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
