import React, { useState, useEffect } from 'react';
import { RefreshCw, Check, AlertCircle } from 'lucide-react';
import { ApprovalCard } from '../components/ui/ApprovalCard';
import { Button } from '../components/ui/Button';
import { api } from '../services/api';
import { invalidateSearchCache } from '../services/search';

export function ApprovalsPage() {
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);
  const [toastType, setToastType] = useState('success');
  const [actionLoadingId, setActionLoadingId] = useState(null);

  const loadApprovals = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getApprovals();
      const list = res.results || res;
      if (Array.isArray(list)) {
        const formatted = list.map(app => {
          const plan = app.repair_plan_detail || app.repair_plan_details || app.repair_plan || {};
          return {
            id: app.id,
            repairId: typeof plan === 'object' ? (plan.id || '') : plan,
            employeeName: app.employee_name || (typeof plan === 'object' && plan.employee_detail && plan.employee_detail.full_name) || (typeof plan === 'object' && plan.employee && plan.employee.full_name) || 'Unknown Employee',
            employeeEmail: app.employee_email || (typeof plan === 'object' && plan.employee_detail && plan.employee_detail.email) || (typeof plan === 'object' && plan.employee && plan.employee.email) || '',
            department: app.employee_department || (typeof plan === 'object' && plan.employee_detail && plan.employee_detail.department) || 'General',
            requestedAction: (typeof plan === 'object' && plan.action) || 'Revoke Access',
            targetSystem: (typeof plan === 'object' && plan.target_system) || 'VPN',
            riskLevel: (typeof plan === 'object' && plan.risk_level) || 'HIGH',
            reason: (typeof plan === 'object' && plan.reason) || 'HR Status is TERMINATED while access remains enabled',
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

  const showToast = (message, type = 'success') => {
    setToastMessage(message);
    setToastType(type);
    setTimeout(() => setToastMessage(null), 5000);
  };

  const handleAction = async (id, actionType) => {
    if (actionLoadingId) return;
    setActionLoadingId(id);
    setToastMessage(null);
    try {
      if (actionType === 'APPROVE') {
        await api.approveRepair(id, 'Approved via ReconcileOS Security Dashboard');
      } else {
        await api.rejectRepair(id, 'Rejected via ReconcileOS Security Dashboard');
      }

      invalidateSearchCache();
      const actionText = actionType === 'APPROVE' ? 'Approved' : 'Rejected';
      showToast(`Decision recorded: ${actionText} approval request.`, 'success');

      await loadApprovals();
    } catch (err) {
      showToast(`Error recording decision: ${err.message}`, 'error');
      await loadApprovals();
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <div className="page-content">
      {/* Editorial Header */}
      <div className="page-header" style={{ marginBottom: '40px' }}>
        <div>
          <div className="page-eyebrow">
            <span className="page-eyebrow-dot" />
            SecOps Governance
          </div>
          <h1 className="page-title">
            <span>Approvals Queue</span>
          </h1>
          <p className="page-subtitle">
            Human-in-the-loop authorization for automated remediation repair plans before execution.
          </p>
        </div>
        <Button variant="secondary" icon={RefreshCw} onClick={loadApprovals} disabled={loading}>
          Refresh Queue
        </Button>
      </div>

      {error && (
        <div
          style={{
            marginBottom: '32px',
            padding: '16px 22px',
            borderRadius: '12px',
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
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {toastMessage && (
        <div
          style={{
            marginBottom: '32px',
            padding: '16px 22px',
            borderRadius: '12px',
            backgroundColor: toastType === 'success'
              ? 'var(--status-healthy-bg)'
              : 'var(--status-critical-bg)',
            border: `1px solid ${toastType === 'success'
              ? 'var(--status-healthy-border)'
              : 'var(--status-critical-border)'}`,
            color: toastType === 'success'
              ? 'var(--status-healthy)'
              : 'var(--status-critical)',
            fontSize: '13px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          {toastType === 'success' ? <Check size={18} /> : <AlertCircle size={18} />}
          <span>{toastMessage}</span>
        </div>
      )}

      {loading && approvals.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px 24px', color: 'var(--text-muted)', fontSize: '14px' }}>
          Loading approval requests...
        </div>
      )}

      {!loading && !error && approvals.length === 0 && (
        <div
          style={{
            textAlign: 'center',
            padding: '60px 24px',
            backgroundColor: '#FFFDF9',
            borderRadius: '16px',
            border: '1px solid rgba(120, 101, 165, 0.12)'
          }}
        >
          <p style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
            No Pending Approvals
          </p>
          <p style={{ fontSize: '14px', color: 'var(--text-muted)', margin: 0 }}>
            All remediation plans have been reviewed or executed. Multi-system access is currently in policy compliance.
          </p>
        </div>
      )}

      {approvals.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
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
              status={app.status}
              isActionLoading={actionLoadingId === app.id}
              isAnyActionLoading={!!actionLoadingId}
              onApprove={() => handleAction(app.id, 'APPROVE')}
              onReject={() => handleAction(app.id, 'REJECT')}
            />
          ))}
        </div>
      )}
    </div>
  );
}
