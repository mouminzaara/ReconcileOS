import React, { useState, useEffect } from 'react';
import { RefreshCw, Play, CheckCircle2, AlertCircle, ShieldCheck } from 'lucide-react';
import { StatusPill } from '../components/ui/StatusPill';
import { Button } from '../components/ui/Button';
import { api } from '../services/api';

/**
 * Backend PlanStatus values:
 *   PENDING, APPROVED, REJECTED, EXECUTING, RETRYING, SUCCESS, COMPLETED, FAILED
 *
 * Execution eligibility (backend-enforced):
 *   - Status must be APPROVED, FAILED, or RETRYING
 *   - Must have an associated ApprovalRequest with decision == APPROVED
 *   - Must not exceed max retry limit
 *
 * Verification eligibility:
 *   - Typically run after SUCCESS or COMPLETED to empirically confirm target state
 */

/** Statuses where the backend permits execution */
const EXECUTABLE_STATUSES = ['APPROVED', 'FAILED', 'RETRYING'];

/** Statuses where verification is meaningful */
const VERIFIABLE_STATUSES = ['SUCCESS', 'COMPLETED'];

function getStatusVariant(status) {
  if (status === 'SUCCESS' || status === 'COMPLETED') return 'healthy';
  if (status === 'EXECUTING' || status === 'RETRYING') return 'warning';
  if (status === 'FAILED') return 'critical';
  if (status === 'REJECTED') return 'critical';
  if (status === 'APPROVED') return 'healthy';
  return 'neutral';
}

export function RepairsPage() {
  const [repairs, setRepairs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoadingId, setActionLoadingId] = useState(null);
  const [actionFeedback, setActionFeedback] = useState(null);

  const loadRepairs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getRepairPlans();
      const list = res.results || res;
      if (Array.isArray(list)) {
        const formatted = list.map(p => ({
          id: `REP-${(p.id || '').substring(0, 8).toUpperCase()}`,
          fullId: p.id,
          employeeName: p.employee_name || (p.employee_detail && p.employee_detail.full_name) || (p.employee && p.employee.full_name) || 'Unknown Employee',
          employeeEmail: p.employee_email || (p.employee_detail && p.employee_detail.email) || (p.employee && p.employee.email) || '',
          targetSystem: p.target_system || 'VPN',
          action: p.action || 'REVOKE_ACCESS',
          actionDetails: p.action_details || `Target connector action: ${p.action}`,
          reason: p.reason || 'HR Status is TERMINATED while access remains enabled',
          riskLevel: p.risk_level || 'HIGH',
          status: p.status || 'PENDING',
          createdAt: p.created_at ? new Date(p.created_at).toLocaleString() : 'Just now'
        }));
        setRepairs(formatted);
      } else {
        setRepairs([]);
      }
    } catch (err) {
      console.error('API error loading repairs:', err);
      setError(err.message || 'Failed to load repair plans from backend.');
      setRepairs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRepairs();
  }, []);

  const clearFeedback = () => {
    setTimeout(() => setActionFeedback(null), 5000);
  };

  const handleExecutePlan = async (fullId) => {
    if (!fullId || actionLoadingId) return;
    setActionLoadingId(fullId);
    setActionFeedback(null);
    try {
      const res = await api.executeRepairPlan(fullId);
      setActionFeedback({
        type: 'success',
        text: res.message || 'Repair plan executed successfully.'
      });
      await loadRepairs();
    } catch (err) {
      setActionFeedback({
        type: 'error',
        text: `Execution failed: ${err.message}`
      });
      await loadRepairs();
    } finally {
      setActionLoadingId(null);
      clearFeedback();
    }
  };

  const handleVerifyPlan = async (fullId) => {
    if (!fullId || actionLoadingId) return;
    setActionLoadingId(fullId);
    setActionFeedback(null);
    try {
      const res = await api.verifyRepairPlan(fullId);
      setActionFeedback({
        type: res.verification_result === 'VERIFIED' ? 'success' : 'warning',
        text: res.message || 'Verification completed.'
      });
      await loadRepairs();
    } catch (err) {
      setActionFeedback({
        type: 'error',
        text: `Verification failed: ${err.message}`
      });
      await loadRepairs();
    } finally {
      setActionLoadingId(null);
      clearFeedback();
    }
  };

  const renderActions = (rep) => {
    const isLoading = actionLoadingId === rep.fullId;
    const status = rep.status;

    if (isLoading) {
      return (
        <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
          Processing…
        </span>
      );
    }

    if (EXECUTABLE_STATUSES.includes(status) && rep.fullId) {
      return (
        <Button
          variant="primary"
          size="small"
          icon={Play}
          onClick={() => handleExecutePlan(rep.fullId)}
          disabled={!!actionLoadingId}
        >
          Execute
        </Button>
      );
    }

    if (VERIFIABLE_STATUSES.includes(status) && rep.fullId) {
      return (
        <Button
          variant="secondary"
          size="small"
          icon={ShieldCheck}
          onClick={() => handleVerifyPlan(rep.fullId)}
          disabled={!!actionLoadingId}
        >
          Verify
        </Button>
      );
    }

    if (status === 'PENDING') {
      return (
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          Awaiting Approval
        </span>
      );
    }

    if (status === 'EXECUTING') {
      return (
        <span style={{ fontSize: '11px', color: 'var(--status-warning)' }}>
          In Progress
        </span>
      );
    }

    return (
      <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>—</span>
    );
  };

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <div className="page-eyebrow">
            <span className="page-eyebrow-dot" />
            <span>Remediation Engine</span>
          </div>
          <h1 className="page-title">Repair Plans</h1>
          <p className="page-subtitle">
            Deterministic access remediation plans generated to self-heal authorization drift
          </p>
        </div>
        <div className="page-header-actions">
          <Button variant="secondary" icon={RefreshCw} onClick={loadRepairs} disabled={loading}>
            Refresh Plans
          </Button>
        </div>
      </div>

      {error && (
        <div
          style={{
            marginBottom: 'var(--space-xl)',
            padding: '14px 20px',
            borderRadius: '10px',
            backgroundColor: 'var(--status-critical-bg)',
            border: '1px solid var(--status-critical-border)',
            color: 'var(--status-critical)',
            fontSize: '13px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {actionFeedback && (
        <div
          style={{
            marginBottom: 'var(--space-xl)',
            padding: '14px 20px',
            borderRadius: '10px',
            backgroundColor: actionFeedback.type === 'success'
              ? 'var(--status-healthy-bg)'
              : actionFeedback.type === 'warning'
                ? 'var(--status-warning-bg)'
                : 'var(--status-critical-bg)',
            border: `1px solid ${actionFeedback.type === 'success'
              ? 'var(--status-healthy-border)'
              : actionFeedback.type === 'warning'
                ? 'var(--status-warning-border)'
                : 'var(--status-critical-border)'}`,
            color: actionFeedback.type === 'success'
              ? 'var(--status-healthy)'
              : actionFeedback.type === 'warning'
                ? 'var(--status-warning)'
                : 'var(--status-critical)',
            fontSize: '13px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          {actionFeedback.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          <span>{actionFeedback.text}</span>
        </div>
      )}

      <div className="editorial-table-container">
        <table className="editorial-table">
          <thead>
            <tr>
              <th>Plan ID</th>
              <th>Employee</th>
              <th>Target System</th>
              <th>Action</th>
              <th>Justification</th>
              <th>Risk</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {repairs.map((rep) => (
              <tr key={rep.id}>
                <td className="font-mono" style={{ padding: '14px 18px', color: 'var(--accent-primary)', fontWeight: 600, fontSize: '12px' }}>
                  {rep.id}
                </td>
                <td style={{ padding: '14px 18px' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{rep.employeeName}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>{rep.employeeEmail}</div>
                </td>
                <td style={{ padding: '14px 18px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 600, padding: '3px 8px', borderRadius: 'var(--radius-pill)', backgroundColor: 'var(--accent-primary-light)', color: 'var(--accent-primary)' }}>
                    {rep.targetSystem}
                  </span>
                </td>
                <td style={{ padding: '14px 18px' }}>
                  <div className="font-mono" style={{ fontWeight: 600, color: 'var(--status-warning)', fontSize: '12px' }}>
                    {rep.action}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>{rep.actionDetails}</div>
                </td>
                <td style={{ padding: '14px 18px', fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '280px', lineHeight: 1.4 }}>
                  {rep.reason}
                </td>
                <td style={{ padding: '14px 18px' }}>
                  <StatusPill status={rep.riskLevel.toLowerCase()} label={rep.riskLevel} size="small" />
                </td>
                <td style={{ padding: '14px 18px' }}>
                  <StatusPill status={getStatusVariant(rep.status)} label={rep.status} size="small" />
                </td>
                <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                  {renderActions(rep)}
                </td>
              </tr>
            ))}
            {repairs.length === 0 && (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '48px 24px', color: 'var(--text-muted)' }}>
                  {loading ? 'Loading repair plans...' : 'No remediation repair plans found. Systems are compliant!'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
