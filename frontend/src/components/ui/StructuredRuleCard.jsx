import React from 'react';
import { StatusPill } from './StatusPill';
import { ArrowRight } from 'lucide-react';

/**
 * StructuredRuleCard — Represents a discrete invariant rule object with condition -> consequence flow.
 * E.g., "If HR = Terminated -> then Access = None"
 */
export function StructuredRuleCard({
  ruleId,
  title,
  condition,
  consequence,
  severity = 'critical',
  status = 'enforced',
  targetSystems = []
}) {
  return (
    <div
      style={{
        backgroundColor: 'var(--bg-surface)',
        borderRadius: 'var(--radius-card)',
        border: '1px solid var(--border-hairline)',
        padding: '22px 26px',
        boxShadow: 'var(--shadow-card)',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }} className="font-mono">
            {ruleId}
          </span>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
            {title}
          </h3>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <StatusPill status={severity.toLowerCase()} label={`Severity: ${severity}`} size="small" />
          <StatusPill status={status.toLowerCase() === 'enforced' ? 'healthy' : 'neutral'} label={status.toUpperCase()} size="small" />
        </div>
      </div>

      {/* Condition -> Consequence Block */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          padding: '14px 18px',
          borderRadius: 'var(--radius-card)',
          backgroundColor: '#F8F5FD',
          border: '1px solid var(--border-hairline)',
          fontSize: '13px'
        }}
      >
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Condition (Invariant Trigger)
          </div>
          <div className="font-mono" style={{ fontWeight: 600, color: 'var(--status-critical)', marginTop: '6px', fontSize: '13px' }}>
            {condition}
          </div>
        </div>

        <ArrowRight size={18} style={{ color: 'var(--accent-primary)', flexShrink: 0, opacity: 0.6 }} />

        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Consequence (Target Enforcement)
          </div>
          <div className="font-mono" style={{ fontWeight: 600, color: 'var(--status-healthy)', marginTop: '6px', fontSize: '13px' }}>
            {consequence}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '13px', color: 'var(--text-muted)' }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Scope:</span>
          {targetSystems.map((sys) => (
            <span
              key={sys}
              style={{
                fontSize: '12px',
                padding: '3px 10px',
                borderRadius: '9999px',
                backgroundColor: 'var(--accent-primary-light)',
                color: 'var(--accent-primary)',
                fontWeight: 600
              }}
            >
              {sys}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
