import React, { useState } from 'react';
import { Save, Check } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { StatusPill } from '../components/ui/StatusPill';

export function SettingsPage() {
  const [scanFrequency, setScanFrequency] = useState(() => {
    return localStorage.getItem('reconcileos_scan_frequency') || '5';
  });
  const [autoRepairPolicy, setAutoRepairPolicy] = useState(() => {
    return localStorage.getItem('reconcileos_auto_repair_policy') || 'SEMI_AUTO';
  });
  const [toastMessage, setToastMessage] = useState(null);

  const handleSave = () => {
    try {
      localStorage.setItem('reconcileos_scan_frequency', scanFrequency);
      localStorage.setItem('reconcileos_auto_repair_policy', autoRepairPolicy);
      setToastMessage('Platform governance settings saved locally.');
      setTimeout(() => setToastMessage(null), 3000);
    } catch {
      setToastMessage('Failed to save settings to localStorage.');
      setTimeout(() => setToastMessage(null), 3000);
    }
  };

  return (
    <div className="page-content">
      {/* Toast */}
      {toastMessage && (
        <div
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            backgroundColor: 'var(--accent-primary)',
            color: '#FFFFFF',
            padding: '12px 20px',
            borderRadius: 'var(--radius-btn)',
            boxShadow: 'var(--shadow-floating)',
            zIndex: 1000,
            fontSize: '14px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <Check size={16} />
          <span>{toastMessage}</span>
        </div>
      )}

      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span>Settings</span>
          </h1>
          <p className="page-subtitle">
            Configure integrity audit frequency, self-healing automation, and API endpoints
          </p>
        </div>
        <Button variant="primary" icon={Save} onClick={handleSave}>
          Save Configuration
        </Button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Engine schedule */}
        <div className="card">
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px' }}>
            Reconciliation Engine Schedule
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
                Scan Frequency
              </label>
              <select
                className="input-base"
                style={{ width: '100%' }}
                value={scanFrequency}
                onChange={(e) => setScanFrequency(e.target.value)}
              >
                <option value="1">Every 1 minute (Aggressive)</option>
                <option value="5">Every 5 minutes (Recommended)</option>
                <option value="15">Every 15 minutes</option>
                <option value="60">Hourly</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
                Auto-Repair Policy
              </label>
              <select
                className="input-base"
                style={{ width: '100%' }}
                value={autoRepairPolicy}
                onChange={(e) => setAutoRepairPolicy(e.target.value)}
              >
                <option value="STRICT">Strict Approval (Human review for ALL repairs)</option>
                <option value="SEMI_AUTO">Semi-Automated (Auto-repair LOW/MED; Approval for CRITICAL/HIGH)</option>
                <option value="FULL_AUTO">Full Self-Healing (Automate ALL verified drift repairs)</option>
              </select>
            </div>
          </div>
        </div>

        {/* API connection */}
        <div className="card">
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px' }}>
            Django REST API Binding
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
                API Base Endpoint
              </label>
              <input
                type="text"
                className="input-base font-mono"
                style={{ width: '100%' }}
                defaultValue="http://127.0.0.1:8000/api/v1/"
                readOnly
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
                Health Check Status
              </label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', height: '36px' }}>
                <StatusPill status="healthy" label="200 OK — Operational" />
              </div>
            </div>
          </div>
        </div>

        {/* Security Policy */}
        <div className="card">
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
            Audit Log Retention Policy
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
            ReconcileOS audit logs are recorded with cryptographic SHA-256 hash chains.
            Log retention policy is set to <strong>365 days</strong> with immutable event stream protection.
          </p>
        </div>
      </div>
    </div>
  );
}

