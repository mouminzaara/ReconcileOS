import React, { useState, useEffect } from 'react';
import { RefreshCw, Check, AlertCircle } from 'lucide-react';
import { ApprovalCard } from '../components/ui/ApprovalCard';
import { Button } from '../components/ui/Button';
import { api } from '../services/api';

export function ApprovalsPage() {
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  const loadApprovals = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getApprovals();
      const list = res.results || res;
      if (Array.isArray(list)) {
        const formatted = list.map(app => {
          const plan = app.repair_plan_details || app.repair_plan || {};
          return {
            id: app.id,
            repairId: typeof plan === 'object' ? (plan.id || '') : plan,
            employeeName: app.employee_name || (plan.employee && plan.employee.full_name) || 'Unknown Employee',
            employeeEmail: app.employee_email || (plan.employee && plan.employee.email) || '',
            department: app.employee_department || (plan.employee && plan.employee.department) || 'General',
            requestedAction: plan.action || 'Revoke Access',
            targetSystem: plan.target_system || 'VPN',
            riskLevel: plan.risk_level || 'HIGH',
            reason: plan.reason || 'HR Status is TERMINATED while access remains enabled',
            requestedAt: app.created_at ? new Date(app.created_at).toLocaleString() : 'Just now',
            status: app.decision || 'PENDING'
          };
        });
        setApprovals(formatted);
      } else {
        setApprovals([]);
      }
    } catch (err) {
      console.error('API error loading approvals:', err);
      setError(err.message || 'Failed to load approvals from backend.');
      setApprovals([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApprovals();
  }, []);

  const handleAction = async (id, actionType) => {
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
      setToastMessage(`Action recorded: ${actionText} approval #${id}`);
      setTimeout(() => setToastMessage(null), 4000);
    } catch (err) {
      setToastMessage(`Error recording decision: ${err.message}`);
    }
  };

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span>Approvals Queue</span>
          </h1>
          <p className="page-subtitle">
            Human-in-the-loop authorization for automated remediation repair plans
          </p>
        </div>
        <Button variant="secondary" icon={RefreshCw} onClick={loadApprovals} disabled={loading}>
          Refresh Queue
        </Button>
      </div>

      {error && (
        <div
          style={{
            marginBottom: '20px',
            padding: '12px 18px',
            borderRadius: 'var(--radius-btn)',
            backgroundColor: 'var(--status-critical-bg)',
            border: '1px solid var(--status-critical-border)',
            color: 'var(--status-critical)',
            fontSize: '13px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {toastMessage && (
        <div
          style={{
            marginBottom: '20px',
            padding: '12px 18px',
            borderRadius: 'var(--radius-btn)',
            backgroundColor: 'var(--status-healthy-bg)',
            border: '1px solid var(--status-healthy-border)',
            color: 'var(--status-healthy)',
            fontSize: '13px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <Check size={16} />
          <span>{toastMessage}</span>
        </div>
      )}

      {!loading && !error && approvals.length === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
          <p style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
            No Pending Approvals
          </p>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            All remediation actions are authorized and up to date.
          </p>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
        {approvals.map((app) => (
          <ApprovalCard
            key={app.id}
            id={app.id}
            employeeName={app.employeeName}
            employeeEmail={app.employeeEmail}
            targetSystem={app.targetSystem}
            requestedAction={app.requestedAction}
            riskLevel={app.riskLevel}
            reason={app.reason}
            requestedAt={app.requestedAt}
            onApprove={() => handleAction(app.id, 'APPROVE')}
            onReject={() => handleAction(app.id, 'REJECT')}
          />
        ))}
      </div>
    </div>
  );
}

