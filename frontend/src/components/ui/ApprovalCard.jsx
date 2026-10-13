import React from 'react';
import { Button } from './Button';
import { StatusPill } from './StatusPill';
import { ShieldAlert, CheckCircle2, XCircle } from 'lucide-react';

/**
 * ApprovalCard — Card component representing a discrete pending approval request.
 * Displays employee context, target system, risk level, requested action, and Approve/Reject buttons.
 */
export function ApprovalCard({
  id,
  employeeName,
  employeeEmail,
  targetSystem,
  requestedAction,
  riskLevel = 'critical',
  reason,
  requestedAt,
  onApprove,
  onReject
}) {
  return (
    <div className="card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
              {employeeName}
            </span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              ({employeeEmail})
            </span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Target: <strong style={{ color: 'var(--text-primary)' }}>{targetSystem}</strong>
          </div>
        </div>
        <StatusPill status={riskLevel.toLowerCase()} label={`Risk: ${riskLevel}`} size="small" />
      </div>

      <div
        style={{
          padding: '12px',
          borderRadius: 'var(--radius-btn)',
          backgroundColor: 'var(--accent-primary-light)',
          border: '1px solid var(--accent-primary-border)'
        }}
      >
        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Requested Action
        </div>
        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px' }}>
          {requestedAction}
        </div>
        {reason && (
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {reason}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '4px' }}>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }} className="font-mono">
          {requestedAt || 'Pending approval'}
        </span>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button variant="secondary" size="small" icon={XCircle} onClick={onReject}>
            Reject
          </Button>
          <Button variant="primary" size="small" icon={CheckCircle2} onClick={onApprove}>
            Approve
          </Button>
        </div>
      </div>
    </div>
  );
}
