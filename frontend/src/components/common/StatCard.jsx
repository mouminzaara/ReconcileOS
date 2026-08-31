import React from 'react';

export function StatCard({ title, value, subtext, icon: Icon, variant = 'info' }) {
  return (
    <div className={`card stat-card ${variant}`}>
      <div className="stat-header">
        <span className="stat-title">{title}</span>
        {Icon && (
          <div className="stat-icon-wrapper">
            <Icon size={18} />
          </div>
        )}
      </div>
      <div className="stat-value">{value}</div>
      {subtext && <div className="stat-subtext">{subtext}</div>}
    </div>
  );
}
