import React, { useState, useEffect } from 'react';
import { CheckCircle2, XCircle, Check, RefreshCw } from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { api } from '../services/api';
import { mockApprovals as initialApprovals } from '../data/mockData';

export function ApprovalsPage() {
  const [approvals, setApprovals] = useState(initialApprovals);
  const [loading, setLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  const loadApprovals = async () => {
    setLoading(true);
    try {
      const res = await api.getApprovals();
      const list = res.results || res;
      if (Array.isArray(list) && list.length > 0) {
        const formatted = list.map(app => {
          const plan = app.repair_plan_details || app.repair_plan || {};
          return {
            id: app.id,
            repairId: typeof plan === 'object' ? (plan.id || 'REP-8042') : plan,
            employeeName: app.employee_name || (plan.employee && plan.employee.full_name) || 'Rahul Kumar',
            employeeEmail: app.employee_email || (plan.employee && plan.employee.email) || 'rahul.kumar@reconcileos.internal',
            department: app.employee_department || 'Engineering',
            requestedAction: plan.action || 'Revoke Access',
            targetSystem: plan.target_system || 'VPN',
            riskLevel: plan.risk_level || 'HIGH',
            reason: plan.reason || 'HR Status is TERMINATED while access remains enabled',
            currentState: {
              hrStatus: 'TERMINATED',
              downstreamState: plan.action || 'ENABLED'
            },
            targetState: {
              hrStatus: 'TERMINATED',
              downstreamState: 'DISABLED / REVOKED'
            },
            requestedAt: app.created_at ? new Date(app.created_at).toLocaleString() : 'Just now',
            status: app.decision || 'PENDING'
          };
        });
        setApprovals(formatted);
      }
    } catch (err) {
      console.warn('API error loading approvals, using mock data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApprovals();
  }, []);

  const handleAction = async (id, actionType) => {
    setActionLoadingId(id);
    try {
      if (actionType === 'APPROVE') {
        await api.approveRepair(id, 'Approved via ReconcileOS Security Dashboard');
      } else {
        await api.rejectRepair(id, 'Rejected via ReconcileOS Security Dashboard');
      }

      setApprovals(prev => prev.map(app => {
        if (app.id === id) {
          return { ...app, status: actionType === 'APPROVE' ? 'APPROVED' : 'REJECTED' };
        }
        return app;
      }));

      const actionText = actionType === 'APPROVE' ? 'Approved' : 'Rejected';
      setToastMessage(`Action successfully recorded: ${actionText} approval #${id}`);
      setTimeout(() => setToastMessage(null), 4000);
    } catch (err) {
      setToastMessage(`Error recording decision: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <CheckCircle2 size={24} style={{ color: 'var(--accent-blue)' }} />
            Human-in-the-Loop Approvals
          </h1>
          <p className="page-subtitle">
            Review and authorize sensitive self-healing repair plans before execution
          </p>
        </div>
        <button className="btn btn-secondary" onClick={loadApprovals} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh Queue
        </button>
      </div>

      {toastMessage && (
        <div style={{
          backgroundColor: 'var(--status-success-bg)',
          border: '1px solid var(--status-success-border)',
          color: 'var(--status-success)',
          padding: '12px 18px',
          borderRadius: 'var(--radius-sm)',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '0.875rem'
        }}>
          <Check size={18} />
          <span>{toastMessage}</span>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {approvals.map((app) => (
          <div key={app.id} className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                  <span className="mono" style={{ color: 'var(--accent-blue)', fontWeight: 700 }}>
                    {app.id}
                  </span>
                  <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Repair Plan: {app.repairId}
                  </span>
                </div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>
                  {app.employeeName} — {app.requestedAction}
                </h3>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {app.employeeEmail} • {app.department}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <SeverityBadge severity={app.riskLevel} />
                <StatusBadge status={app.status} />
              </div>
            </div>

            <div style={{
              background: 'var(--bg-card-secondary)',
              padding: '12px 16px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)',
              marginBottom: '16px',
              fontSize: '0.85rem',
              color: 'var(--text-secondary)'
            }}>
              <strong style={{ color: 'var(--text-main)' }}>Justification / Trigger Reason:</strong> {app.reason}
            </div>

            {/* State Diffs (Current vs Desired) */}
            <div className="state-diff-container">
              <div className="state-diff-box current">
                <div className="diff-box-title">Current State (Violating Drift)</div>
                {Object.entries(app.currentState).map(([k, v]) => (
                  <div key={k} className="diff-line">
                    <span style={{ color: 'var(--text-muted)' }}>{k}:</span>
                    <span className="mono" style={{ fontWeight: 600 }}>{String(v)}</span>
                  </div>
                ))}
              </div>

              <div className="state-diff-box desired">
                <div className="diff-box-title">Target State (Post-Repair Verification)</div>
                {Object.entries(app.targetState).map(([k, v]) => (
                  <div key={k} className="diff-line">
                    <span style={{ color: 'var(--text-muted)' }}>{k}:</span>
                    <span className="mono" style={{ fontWeight: 600 }}>{String(v)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Bar */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: '16px',
              paddingTop: '14px',
              borderTop: '1px solid var(--border-color)'
            }}>
              <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Requested At: {app.requestedAt}
              </span>

              {app.status === 'PENDING' ? (
                <div style={{ display: 'flex', gap: '12px' }}>
                  <button
                    className="btn btn-danger"
                    onClick={() => handleAction(app.id, 'REJECT')}
                    disabled={actionLoadingId === app.id}
                  >
                    <XCircle size={16} /> Reject Action
                  </button>
                  <button
                    className="btn btn-success"
                    onClick={() => handleAction(app.id, 'APPROVE')}
                    disabled={actionLoadingId === app.id}
                  >
                    <CheckCircle2 size={16} /> Approve & Execute
                  </button>
                </div>
              ) : (
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: app.status === 'APPROVED' ? 'var(--status-success)' : 'var(--status-danger)' }}>
                  Decision Recorded ({app.status})
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
