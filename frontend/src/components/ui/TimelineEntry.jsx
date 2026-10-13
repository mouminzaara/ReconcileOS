import React from 'react';

/**
 * TimelineEntry — Vertical timeline item.
 * Vertical line with status-colored dot, monospace timestamp, and plain-language description.
 */
export function TimelineEntry({
  timestamp,
  title,
  description,
  status = 'neutral',
  isLast = false
}) {
  const dotColorMap = {
    critical: 'var(--status-critical)',
    warning: 'var(--status-warning)',
    healthy: 'var(--status-healthy)',
    neutral: 'var(--status-neutral)'
  };

  const dotColor = dotColorMap[status.toLowerCase()] || dotColorMap.neutral;

  return (
    <div style={{ display: 'flex', gap: '16px', position: 'relative' }}>
      {/* Vertical line & Dot column */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: '16px' }}>
        <div
          style={{
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            backgroundColor: dotColor,
            border: `2px solid var(--bg-surface)`,
            boxShadow: `0 0 0 2px ${dotColor}`,
            zIndex: 2,
            marginTop: '4px'
          }}
        />
        {!isLast && (
          <div
            style={{
              width: '2px',
              flex: 1,
              backgroundColor: 'var(--border-hairline)',
              marginTop: '4px',
              marginBottom: '4px'
            }}
          />
        )}
      </div>

      {/* Content column */}
      <div style={{ paddingBottom: isLast ? '0' : '20px', flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
            {title}
          </span>
          {timestamp && (
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }} className="font-mono">
              {timestamp}
            </span>
          )}
        </div>
        {description && (
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {description}
          </div>
        )}
      </div>
    </div>
  );
}
