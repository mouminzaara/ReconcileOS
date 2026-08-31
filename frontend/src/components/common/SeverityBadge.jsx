import React from 'react';
import { AlertCircle, AlertTriangle, Info } from 'lucide-react';

export function SeverityBadge({ severity }) {
  const normalized = (severity || '').toUpperCase();

  let badgeClass = 'badge-info';
  let Icon = Info;

  if (normalized === 'CRITICAL') {
    badgeClass = 'badge-critical';
    Icon = AlertCircle;
  } else if (normalized === 'HIGH') {
    badgeClass = 'badge-warning';
    Icon = AlertTriangle;
  } else if (normalized === 'MEDIUM') {
    badgeClass = 'badge-info';
    Icon = Info;
  }

  return (
    <span className={`badge ${badgeClass}`}>
      <Icon size={12} />
      {severity}
    </span>
  );
}
