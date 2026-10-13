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
    neutral: 'var(--status-neutral)'
  };

  const accentColor = accentColorMap[status] || accentColorMap.neutral;

  return (
    <div
      className="card"
      style={{
        position: 'relative',
        overflow: 'hidden',
        paddingTop: '22px'
      }}
    >
      {/* Top accent bar */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '4px',
          backgroundColor: accentColor
        }}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)' }}>
          {title}
        </span>
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
              color: 'var(--accent-primary)'
            }}
          >
            <Icon size={16} />
          </div>
        )}
      </div>

      <div style={{ fontSize: '28px', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2, letterSpacing: '-0.02em' }}>
        {value}
      </div>

      {(statusLabel || subtext) && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px', fontSize: '12px' }}>
          {statusLabel && (
            <span
              style={{
                fontWeight: 600,
                color: accentColor
              }}
            >
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
