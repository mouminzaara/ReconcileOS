import React from 'react';

/**
 * StatCard — Big number metric + label + status accent bar.
 * Accepts:
 * - title: string
 * - value: string | number
 * - status: 'critical' | 'warning' | 'healthy' | 'neutral' (default 'neutral')
 * - statusLabel: string (optional explicit status text)
 * - icon: React component (optional)
 * - subtext: string (optional detail)
 */
export function StatCard({
  title,
  value,
  status = 'neutral',
  statusLabel,
  icon: Icon,
  subtext
}) {
  const accentColorMap = {
    critical: 'var(--status-critical)',
    warning: 'var(--status-warning)',
    healthy: 'var(--status-healthy)',
    neutral: 'var(--text-muted)'
  };

  const accentColor = accentColorMap[status] || accentColorMap.neutral;

  return (
    <div
      className="card"
      style={{
        position: 'relative',
        overflow: 'hidden',
        padding: '20px 20px 16px',
      }}
    >
      {/* Subtle left accent stripe */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '3px',
          height: '100%',
          backgroundColor: accentColor,
          opacity: 0.5
        }}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
        <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.02em' }}>
          {title}
        </span>
        {Icon && (
          <Icon size={15} style={{ color: 'var(--text-muted)', opacity: 0.6 }} />
        )}
      </div>

      <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2, letterSpacing: '-0.02em', marginTop: '4px' }}>
        {value}
      </div>

      {(statusLabel || subtext) && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', fontSize: '11px' }}>
          {statusLabel && (
            <span style={{ fontWeight: 600, color: accentColor }}>
              {statusLabel}
            </span>
          )}
          {subtext && (
            <span style={{ color: 'var(--text-muted)' }}>
              {subtext}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
