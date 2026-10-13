import React from 'react';

/**
 * StatusPill — Dot + label text pill.
 * Statuses: 'critical' | 'warning' | 'healthy' | 'neutral'
 * Pairs dot indicator + label text (never color alone).
 */
export function StatusPill({ status = 'neutral', label, size = 'medium' }) {
  const stylesMap = {
    critical: {
      bg: 'var(--status-critical-bg)',
      color: 'var(--status-critical)',
      border: 'var(--status-critical-border)',
      dot: 'var(--status-critical)'
    },
    warning: {
      bg: 'var(--status-warning-bg)',
      color: 'var(--status-warning)',
      border: 'var(--status-warning-border)',
      dot: 'var(--status-warning)'
    },
    healthy: {
      bg: 'var(--status-healthy-bg)',
      color: 'var(--status-healthy)',
      border: 'var(--status-healthy-border)',
      dot: 'var(--status-healthy)'
    },
    neutral: {
      bg: 'var(--status-neutral-bg)',
      color: 'var(--status-neutral)',
      border: 'var(--status-neutral-border)',
      dot: 'var(--status-neutral)'
    }
  };

  // Map legacy string badges if needed
  let normalizedStatus = status.toLowerCase();
  if (['active', 'enforced', 'verified'].includes(normalizedStatus)) normalizedStatus = 'healthy';
  if (['terminated', 'disabled', 'revoked'].includes(normalizedStatus)) normalizedStatus = 'neutral';
  if (['drift_detected', 'high', 'medium', 'pending'].includes(normalizedStatus)) normalizedStatus = 'warning';

  const styleConfig = stylesMap[normalizedStatus] || stylesMap.neutral;
  const displayLabel = label || status;

  const isSmall = size === 'small';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: isSmall ? '5px' : '6px',
        padding: isSmall ? '2px 8px' : '4px 10px',
        borderRadius: 'var(--radius-pill)',
        backgroundColor: styleConfig.bg,
        color: styleConfig.color,
        border: `1px solid ${styleConfig.border}`,
        fontSize: isSmall ? '11px' : '12px',
        fontWeight: 600,
        letterSpacing: '0.01em',
        lineHeight: 1,
        whiteSpace: 'nowrap'
      }}
    >
      <span
        style={{
          width: isSmall ? '6px' : '7px',
          height: isSmall ? '6px' : '7px',
          borderRadius: '50%',
          backgroundColor: styleConfig.dot,
          flexShrink: 0
        }}
      />
      <span>{displayLabel}</span>
    </span>
  );
}
