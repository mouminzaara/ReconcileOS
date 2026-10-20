import React, { useState, useEffect } from 'react';
import { Save, Check, RefreshCw, Info, Lock } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { StatusPill } from '../components/ui/StatusPill';
import { api } from '../services/api';

export function SettingsPage() {
  const [scanFrequency, setScanFrequency] = useState(() => {
    return localStorage.getItem('reconcileos_scan_frequency') || '5';
  });
  const [toastMessage, setToastMessage] = useState(null);

  // Live Backend Health State
  const [healthLoading, setHealthLoading] = useState(true);
  const [healthData, setHealthData] = useState(null);
  const [healthError, setHealthError] = useState(null);

  const checkBackendHealth = async () => {
    setHealthLoading(true);
    setHealthError(null);
    try {
      const res = await api.getHealth();
      setHealthData(res);
    } catch (err) {
      console.error('Health check failed:', err);
      setHealthError(err.message || 'Backend API unreachable');
      setHealthData(null);
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    checkBackendHealth();
  }, []);

  const handleSave = () => {
    try {
      localStorage.setItem('reconcileos_scan_frequency', scanFrequency);
      setToastMessage('Browser preferences saved locally. (Backend governance policies remain server-enforced).');
      setTimeout(() => setToastMessage(null), 4000);
    } catch {
      setToastMessage('Failed to save preferences to localStorage.');
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  return (
    <div className="page-content">
      {/* Toast Notification */}
      {toastMessage && (
        <div
          style={{
            position: 'fixed',
            bottom: '32px',
            right: '32px',
            backgroundColor: 'var(--accent-primary)',
            color: '#FFFFFF',
            padding: '14px 24px',
            borderRadius: '9999px',
            boxShadow: '0 8px 30px rgba(120, 101, 165, 0.25)',
            zIndex: 1000,
            fontSize: '13px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          <Check size={18} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Editorial Header */}
      <div className="page-header" style={{ marginBottom: '40px' }}>
        <div>
          <div className="page-eyebrow">
            <span className="page-eyebrow-dot" />
            System Configuration
          </div>
          <h1 className="page-title">
            <span>Platform Settings & Governance Reality</span>
          </h1>
          <p className="page-subtitle">
            Configure local client preferences and review server-enforced zero-trust governance policies.
          </p>
        </div>
        <Button variant="primary" icon={Save} onClick={handleSave}>
          Save Local Preferences
        </Button>
      </div>

      {/* Governance & Architecture Notice */}
      <div
        style={{
          marginBottom: '40px',
          padding: '24px 28px',
          borderRadius: '16px',
          backgroundColor: '#FFFDF9',
          border: '1px solid rgba(120, 101, 165, 0.18)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.02)',
          display: 'flex',
          gap: '18px',
          alignItems: 'flex-start'
        }}
      >
        <div
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            backgroundColor: 'var(--accent-primary-light)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--accent-primary)',
            flexShrink: 0,
            marginTop: '2px'
          }}
        >
          <Info size={18} />
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)', marginBottom: '6px' }}>
            Settings Reality & Persistence Notice
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: '1.6' }}>
            ReconcileOS separates <strong>browser-local preferences</strong> (stored solely in your browser's localStorage)
            from <strong>server-enforced security policies</strong> (immutable audit trails, RBAC, and mandatory human approval).
            Local preferences do not control background daemon schedules or bypass server governance.
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '48px' }}>
        {/* 1. Client Scan Preference */}
        <section
          style={{
            backgroundColor: '#FFFDF9',
            borderRadius: '16px',
            border: '1px solid rgba(120, 101, 165, 0.12)',
            padding: '32px 36px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.02)'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                Reconciliation Audit Cadence
              </h3>
              <p style={{ fontSize: '14px', color: 'var(--text-muted)', margin: 0 }}>
                Client-side interval preference for automated multi-system telemetry polling
              </p>
            </div>
            <StatusPill status="neutral" label="Browser-local preference" size="small" />
          </div>

          <div style={{ maxWidth: '440px', marginBottom: '20px' }}>
            <label
              htmlFor="scan-cadence-select"
              style={{
                display: 'block',
                fontSize: '11px',
                fontWeight: 700,
                color: 'var(--text-muted)',
                marginBottom: '8px',
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}
            >
              Polling Cadence
            </label>
            <select
              id="scan-cadence-select"
              className="input-base"
              style={{ width: '100%', padding: '12px 16px', fontSize: '14px', borderRadius: '9999px', backgroundColor: 'var(--bg-base)' }}
              value={scanFrequency}
              onChange={(e) => setScanFrequency(e.target.value)}
            >
              <option value="1">Every 1 minute (Aggressive)</option>
              <option value="5">Every 5 minutes (Recommended)</option>
              <option value="15">Every 15 minutes</option>
              <option value="60">Hourly</option>
            </select>
          </div>

          <div
            style={{
              padding: '16px 20px',
              borderRadius: '12px',
              backgroundColor: 'var(--bg-base)',
              border: '1px solid var(--border-hairline)',
              fontSize: '13px',
              color: 'var(--text-secondary)',
              lineHeight: '1.6'
            }}
          >
            <strong>Implementation Status:</strong> No automated background scheduler daemon (Celery / cron) is currently running
            in this development deployment. Audit cycles are executed on demand via the Dashboard ("Run Reconciliation Audit") or via backend CLI:
            <code style={{ marginLeft: '6px', padding: '3px 8px', backgroundColor: '#FFFFFF', border: '1px solid var(--border-hairline)', borderRadius: '6px' }}>
              python manage.py run_continuous_monitor
            </code>.
          </div>
        </section>

        {/* 2. Self-Healing & Governance Enforcement */}
        <section
          style={{
            backgroundColor: '#FFFDF9',
            borderRadius: '16px',
            border: '1px solid rgba(120, 101, 165, 0.12)',
            padding: '32px 36px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.02)'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                Remediation Governance Policy
              </h3>
              <p style={{ fontSize: '14px', color: 'var(--text-muted)', margin: 0 }}>
                Policy governing the execution of automated drift remediation repair plans
              </p>
            </div>
            <StatusPill status="healthy" label="Mandatory Human Review" size="small" />
          </div>

          <div style={{ maxWidth: '440px', marginBottom: '20px' }}>
            <label
              htmlFor="governance-policy-select"
              style={{
                display: 'block',
                fontSize: '11px',
                fontWeight: 700,
                color: 'var(--text-muted)',
                marginBottom: '8px',
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}
            >
              Repair Authorization Mode
            </label>
            <div style={{ position: 'relative' }}>
              <select
                id="governance-policy-select"
                className="input-base"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  fontSize: '14px',
                  borderRadius: '9999px',
                  backgroundColor: 'var(--bg-base)',
                  cursor: 'not-allowed',
                  opacity: 0.8
                }}
                disabled={true}
                value="STRICT"
              >
                <option value="STRICT">Strict Human Approval (Mandatory for ALL repairs)</option>
              </select>
              <Lock size={16} style={{ position: 'absolute', right: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            </div>
          </div>

          <div
            style={{
              padding: '16px 20px',
              borderRadius: '12px',
              backgroundColor: 'var(--bg-base)',
              border: '1px solid var(--status-healthy-border)',
              fontSize: '13px',
              color: 'var(--text-secondary)',
              lineHeight: '1.6'
            }}
          >
            <strong style={{ color: 'var(--status-healthy)' }}>Backend Enforced (Phase 2A):</strong> The ReconcileOS backend strictly enforces human-in-the-loop review.
            Any repair plan requiring authorization must be explicitly approved in the Approvals Queue before execution.
            Unconditional automatic approval (<code style={{ padding: '2px 6px', borderRadius: '4px' }}>auto_approve=true</code>) is rejected by the backend API.
          </div>
        </section>

        {/* 3. Live Django REST API Core Binding */}
        <section
          style={{
            backgroundColor: '#FFFDF9',
            borderRadius: '16px',
            border: '1px solid rgba(120, 101, 165, 0.12)',
            padding: '32px 36px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.02)'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                Backend REST API Binding
              </h3>
              <p style={{ fontSize: '14px', color: 'var(--text-muted)', margin: 0 }}>
                Target Django REST Framework core endpoint and verified service health
              </p>
            </div>
            <Button
              variant="secondary"
              icon={RefreshCw}
              onClick={checkBackendHealth}
              disabled={healthLoading}
            >
              {healthLoading ? 'Probing...' : 'Check Health'}
            </Button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px', marginBottom: '16px' }}>
            <div>
              <label
                htmlFor="api-endpoint-input"
                style={{
                  display: 'block',
                  fontSize: '11px',
                  fontWeight: 700,
                  color: 'var(--text-muted)',
                  marginBottom: '8px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}
              >
                Configured Base Endpoint
              </label>
              <input
                id="api-endpoint-input"
                type="text"
                className="input-base font-mono"
                style={{ width: '100%', fontSize: '13px', padding: '12px 16px', borderRadius: '9999px', backgroundColor: 'var(--bg-base)' }}
                defaultValue="http://127.0.0.1:8000/api/v1/"
                readOnly
              />
            </div>

            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: '11px',
                  fontWeight: 700,
                  color: 'var(--text-muted)',
                  marginBottom: '8px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}
              >
                Live Health Verification
              </label>
              <div style={{ display: 'flex', alignItems: 'center', height: '44px' }}>
                {healthLoading ? (
                  <StatusPill status="neutral" label="Probing /api/v1/health/..." />
                ) : healthData ? (
                  <StatusPill
                    status="healthy"
                    label={`200 OK — ${healthData.service || 'API Core'} v${healthData.version || '0.1.0'}`}
                  />
                ) : (
                  <StatusPill
                    status="critical"
                    label={`Unreachable (${healthError || 'Error'})`}
                  />
                )}
              </div>
            </div>
          </div>

          {healthData && Array.isArray(healthData.active_modules) && (
            <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Active backend modules: <span className="font-mono" style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{healthData.active_modules.join(', ')}</span>
            </div>
          )}
        </section>

        {/* 4. Security & Cryptographic Audit Stream Reality */}
        <section
          style={{
            backgroundColor: '#FFFDF9',
            borderRadius: '16px',
            border: '1px solid rgba(120, 101, 165, 0.12)',
            padding: '32px 36px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.02)'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                Security & Audit Retention Architecture
              </h3>
              <p style={{ fontSize: '14px', color: 'var(--text-muted)', margin: 0 }}>
                Cryptographic tamper-evidence and identity role policies
              </p>
            </div>
            <StatusPill status="healthy" label="SHA-256 Hash Chained" size="small" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px' }}>
            <div
              style={{
                padding: '24px',
                borderRadius: '12px',
                backgroundColor: 'var(--bg-base)',
                border: '1px solid var(--border-hairline)',
                fontSize: '13px'
              }}
            >
              <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px', fontSize: '14px' }}>
                Immutable Audit Log Chains
              </div>
              <div style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                Audit events calculate backward SHA-256 hashes linking each record to its predecessor.
                Cryptographic integrity is verifiable via the Audit page. Retention is indefinite (automated log pruning is not implemented).
              </div>
            </div>

            <div
              style={{
                padding: '24px',
                borderRadius: '12px',
                backgroundColor: 'var(--bg-base)',
                border: '1px solid var(--border-hairline)',
                fontSize: '13px'
              }}
            >
              <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px', fontSize: '14px' }}>
                Role-Based Access Control (RBAC)
              </div>
              <div style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                Enforced server-side via Django REST Framework permission classes (ADMIN, OPERATOR, VIEWER).
                Authenticated requests use SimpleJWT Bearer tokens with short-lived access lifespans.
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
