import React from 'react';
import { StatusPill } from './StatusPill';
import { ArrowRight, ShieldCheck } from 'lucide-react';

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
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }} className="font-mono">
            {ruleId}
          </span>
          <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
            {title}
          </h4>
        </div>
        <StatusPill status={severity.toLowerCase()} label={`Severity: ${severity}`} size="small" />
      </div>

      {/* Condition -> Consequence Block */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '12px 14px',
          borderRadius: 'var(--radius-btn)',
          backgroundColor: 'var(--bg-base)',
          border: '1px solid var(--border-hairline)',
          fontSize: '13px'
        }}
      >
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            IF (Condition)
          </div>
          <div style={{ fontWeight: 600, color: 'var(--status-critical)', marginTop: '2px' }}>
            {condition}
          </div>
        </div>

        <ArrowRight size={16} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />

        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            THEN (Consequence)
          </div>
          <div style={{ fontWeight: 600, color: 'var(--status-healthy)', marginTop: '2px' }}>
            {consequence}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', color: 'var(--text-muted)' }}>
        <div style={{ display: 'flex', gap: '6px' }}>
          {targetSystems.map((sys) => (
            <span
              key={sys}
              style={{
                fontSize: '11px',
                padding: '2px 6px',
                borderRadius: 'var(--radius-btn)',
                backgroundColor: 'var(--accent-primary-light)',
                color: 'var(--accent-primary)',
                fontWeight: 600
              }}
            >
              {sys}
            </span>
          ))}
        </div>
        <StatusPill status="healthy" label={status.toUpperCase()} size="small" />
      </div>
    </div>
  );
}
