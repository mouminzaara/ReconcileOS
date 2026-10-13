import React from 'react';
import { StatusPill } from './StatusPill';

/**
 * ActivityRow — Plain divided row (not a card).
 * Contains: icon, description text, monospace timestamp, right-aligned status pill.
 */
export function ActivityRow({
  icon: Icon,
  description,
  timestamp,
  status = 'neutral',
  statusLabel
}) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        borderBottom: '1px solid var(--border-hairline)',
        backgroundColor: 'var(--bg-surface)',
        transition: 'background-color 0.15s ease'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0, flex: 1 }}>
        {Icon && (
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: 'var(--radius-btn)',
              backgroundColor: 'var(--accent-primary-light)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-primary)',
              flexShrink: 0
            }}
          >
            <Icon size={16} />
          </div>
        )}
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
            {description}
          </div>
          {timestamp && (
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }} className="font-mono">
              {timestamp}
            </div>
          )}
        </div>
      </div>

      <div style={{ marginLeft: '16px', flexShrink: 0 }}>
        <StatusPill status={status} label={statusLabel || status} size="small" />
      </div>
    </div>
  );
}
