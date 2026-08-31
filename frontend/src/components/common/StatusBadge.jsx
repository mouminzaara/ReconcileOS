import React from 'react';

export function StatusBadge({ status }) {
  const normalized = (status || '').toUpperCase();

  let badgeClass = 'badge-info';
  if (['ACTIVE', 'HEALTHY', 'SUCCESS', 'ENFORCED', 'ENABLED', 'RESOLVED'].includes(normalized)) {
    badgeClass = 'badge-active';
  } else if (['TERMINATED', 'DISABLED', 'CRITICAL', 'FAILED', 'REVOKED'].includes(normalized)) {
    badgeClass = 'badge-terminated';
  } else if (['DRIFT_DETECTED', 'WARNING', 'PENDING', 'PENDING_APPROVAL'].includes(normalized)) {
    badgeClass = 'badge-warning';
  } else if (['EXECUTING', 'IN_PROGRESS', 'DRY_RUN'].includes(normalized)) {
    badgeClass = 'badge-info';
  }

  return (
    <span className={`badge ${badgeClass}`}>
      {status}
    </span>
  );
}
