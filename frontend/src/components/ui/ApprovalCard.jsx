import React from 'react';
import { Button } from './Button';
import { StatusPill } from './StatusPill';
import { CheckCircle2, XCircle } from 'lucide-react';

/**
 * ApprovalCard — Card component representing a discrete pending approval request.
 * Displays employee context, target system, risk level, requested action, and Approve/Reject buttons.
 * Buttons are disabled when the decision has already been made, or when an action is in progress.
 */
export function ApprovalCard({
  employeeName,
  employeeEmail,
  targetSystem,
  requestedAction,
  riskLevel = 'critical',
  reason,
  requestedAt,
  status = 'PENDING',
  isActionLoading = false,
  isAnyActionLoading = false,
  onApprove,
  onReject
}) {
  const isPending = status === 'PENDING';
  const isDecided = status === 'APPROVED' || status === 'REJECTED';
  const actionsDisabled = !isPending || isActionLoading || isAnyActionLoading;

  return (
    <div
      style={{
        backgroundColor: '#FFFDF9',
        borderRadius: '16px',
        border: '1px solid rgba(120, 101, 165, 0.12)',
        padding: '32px 36px',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.02)',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              {employeeName}
            </h3>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              ({employeeEmail})
            </span>
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Downstream Target: <strong style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>{targetSystem}</strong>
          </div>
        </div>
        <StatusPill status={riskLevel.toLowerCase()} label={`Risk: ${riskLevel}`} size="small" />
      </div>

      <div
        style={{
          padding: '18px 22px',
          borderRadius: '12px',
          backgroundColor: 'var(--bg-base)',
          border: '1px solid var(--border-hairline)'
        }}
      >
        <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Remediation Action Required
        </div>
        <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px' }}>
          {requestedAction}
        </div>
        {reason && (
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '6px', lineHeight: '1.5' }}>
            {reason}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '4px' }}>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }} className="font-mono">
          Requested: {requestedAt || 'Pending review'}
        </span>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {isDecided ? (
            <StatusPill
              status={status === 'APPROVED' ? 'healthy' : 'critical'}
              label={status}
              size="small"
            />
          ) : isActionLoading ? (
            <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
              Processing decision…
            </span>
          ) : (
            <>
              <Button variant="secondary" icon={XCircle} onClick={onReject} disabled={actionsDisabled}>
                Reject
              </Button>
              <Button variant="primary" icon={CheckCircle2} onClick={onApprove} disabled={actionsDisabled}>
                Approve & Execute
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
