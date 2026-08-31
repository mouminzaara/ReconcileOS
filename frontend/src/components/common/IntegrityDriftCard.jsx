import React from 'react';
import {
  ShieldAlert,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Zap,
  Play,
  Cpu,
  ShieldCheck,
  FileCheck
} from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { SeverityBadge } from './SeverityBadge';

export function IntegrityDriftCard({ onRunAudit, onRunMonitor, actionLoading }) {
  return (
    <div
      className="card"
      style={{
        marginBottom: '28px',
        border: '1px solid var(--border-color)',
        background: 'var(--bg-card)',
        boxShadow: 'var(--shadow-md)',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Top Accent Line */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          background: 'linear-gradient(90deg, #C62828 0%, #D84315 50%, #2E7D32 100%)'
        }}
      />

      {/* Header Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid var(--border-color)',
          paddingBottom: '14px',
          marginBottom: '20px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--status-danger-bg)',
              border: '1px solid var(--status-danger-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--status-danger)'
            }}
          >
            <ShieldAlert size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>
                Active Integrity & Authorization Drift Showcase
              </h2>
              <span className="badge badge-critical" style={{ fontSize: '0.68rem' }}>
                LIVE DRIFT DETECTED
              </span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Invariant Rule #INV-RULE-002: Terminated employees must not retain active target system access
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.78rem', padding: '6px 12px' }}
            onClick={onRunAudit}
            disabled={actionLoading}
          >
            <Zap size={14} style={{ color: 'var(--status-warning)' }} /> Audit Drift
          </button>
          <button
            className="btn btn-primary"
            style={{ fontSize: '0.78rem', padding: '6px 14px' }}
            onClick={onRunMonitor}
            disabled={actionLoading}
          >
            <Play size={14} /> Execute Self-Healing
          </button>
        </div>
      </div>

      {/* Visual System State Comparison Flow */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr auto 1fr auto 1.2fr',
          gap: '16px',
          alignItems: 'center',
          background: 'var(--bg-card-secondary)',
          borderRadius: 'var(--radius-md)',
          padding: '20px',
          border: '1px solid var(--border-color)',
          marginBottom: '20px'
        }}
      >
        {/* Source System (HR) */}
        <div
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-sm)',
            padding: '14px',
            textAlign: 'center'
          }}
        >
          <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--accent-blue)', textTransform: 'uppercase', marginBottom: '4px', fontWeight: 600 }}>
            Source of Record (HR)
          </div>
          <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-main)', marginBottom: '2px' }}>
            Rahul Kumar
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '10px' }}>
            rahul.kumar@reconcileos.internal
          </div>
          <div style={{ display: 'inline-flex', gap: '6px', alignItems: 'center', background: 'var(--status-danger-bg)', border: '1px solid var(--status-danger-border)', padding: '4px 10px', borderRadius: '999px' }}>
            <span className="mono" style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--status-danger)' }}>
              HR: TERMINATED
            </span>
          </div>
        </div>

        {/* Conflict Icon */}
        <div style={{ color: 'var(--status-danger)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
          <AlertTriangle size={22} className="spin-slow" />
          <span className="mono" style={{ fontSize: '0.65rem', color: 'var(--status-danger)', fontWeight: 700 }}>
            VS
          </span>
        </div>

        {/* Target System (GitHub / VPN / Cloud / Slack) */}
        <div
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--status-warning-border)',
            borderRadius: 'var(--radius-sm)',
            padding: '14px',
            textAlign: 'center'
          }}
        >
          <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--status-warning)', textTransform: 'uppercase', marginBottom: '4px', fontWeight: 600 }}>
            Target Gateway (Downstream)
          </div>
          <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-main)', marginBottom: '2px' }}>
            GitHub / VPN / Cloud / Slack
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '10px' }}>
            Username: rahulkumar_gh
          </div>
          <div style={{ display: 'inline-flex', gap: '6px', alignItems: 'center', background: 'var(--status-warning-bg)', border: '1px solid var(--status-warning-border)', padding: '4px 10px', borderRadius: '999px' }}>
            <span className="mono" style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--status-warning)' }}>
              STATE: ACTIVE / MEMBER
            </span>
          </div>
        </div>

        {/* Transition Arrow */}
        <div style={{ color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <ArrowRight size={26} />
        </div>

        {/* Detected Integrity Violation & Diffs */}
        <div
          style={{
            background: 'var(--status-danger-bg)',
            border: '1px solid var(--status-danger-border)',
            borderRadius: 'var(--radius-sm)',
            padding: '14px'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span className="mono" style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--status-danger)' }}>
              DRIFT ANOMALY EVALUATION
            </span>
            <SeverityBadge severity="CRITICAL" />
          </div>

          <div style={{ fontSize: '0.78rem', marginBottom: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Expected State:</span>
              <span className="mono" style={{ color: 'var(--status-success)', fontWeight: 700 }}>
                REVOKED / DISABLED
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Actual State:</span>
              <span className="mono" style={{ color: 'var(--status-danger)', fontWeight: 700 }}>
                ACTIVE / MEMBER
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 5-Stage Visual Reconciliation Pipeline */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(5, 1fr)',
          gap: '12px',
          paddingTop: '6px'
        }}
      >
        <div className="pipeline-step completed">
          <div className="step-badge">1. Detected</div>
          <div className="step-desc">Drift identified by rule engine</div>
        </div>

        <div className="pipeline-step completed">
          <div className="step-badge">2. Planned</div>
          <div className="step-desc">Deterministic repair generated</div>
        </div>

        <div className="pipeline-step active">
          <div className="step-badge">3. Approval</div>
          <div className="step-desc">Human-in-the-loop SecOps review</div>
        </div>

        <div className="pipeline-step pending">
          <div className="step-badge">4. Execution</div>
          <div className="step-desc">Target connector API action</div>
        </div>

        <div className="pipeline-step pending">
          <div className="step-badge">5. Verification</div>
          <div className="step-desc">Empirical post-repair audit</div>
        </div>
      </div>
    </div>
  );
}
