import React from 'react';
import { Settings, Shield, Sliders, Bell, Database, Lock, Save } from 'lucide-react';

export function SettingsPage() {
  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Settings size={24} style={{ color: 'var(--accent-blue)' }} />
            Platform & Governance Settings
          </h1>
          <p className="page-subtitle">
            Configure integrity audit intervals, self-healing automation, and notification webhooks
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => alert('Settings saved successfully (Mock)!')}>
          <Save size={14} /> Save Configuration
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* Audit Schedule & Automation */}
        <div className="card">
          <div className="card-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Sliders size={18} style={{ color: 'var(--accent-cyan)' }} />
              <span>Reconciliation Engine Schedule</span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                Continuous Scan Frequency (minutes)
              </label>
              <select className="search-input" style={{ width: '100%', paddingLeft: '12px' }} defaultValue="5">
                <option value="1">Every 1 minute (Aggressive)</option>
                <option value="5">Every 5 minutes (Recommended)</option>
                <option value="15">Every 15 minutes</option>
                <option value="60">Hourly</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                Auto-Repair Threshold Policy
              </label>
              <select className="search-input" style={{ width: '100%', paddingLeft: '12px' }} defaultValue="SEMI_AUTO">
                <option value="STRICT">Strict Approval (Human review for ALL repairs)</option>
                <option value="SEMI_AUTO">Semi-Automated (Auto-repair LOW/MED risk; Approval for CRITICAL/HIGH)</option>
                <option value="FULL_AUTO">Full Self-Healing (Automate ALL verified drift repairs)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Backend Endpoint Settings */}
        <div className="card">
          <div className="card-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Database size={18} style={{ color: 'var(--status-success)' }} />
              <span>Django REST API Connection (Future Milestone Binding)</span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                Django REST Base URL
              </label>
              <input
                type="text"
                className="search-input mono"
                style={{ paddingLeft: '12px' }}
                defaultValue="http://127.0.0.1:8000/api/v1/"
                readOnly
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                API Health Endpoint Status
              </label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', height: '36px' }}>
                <span className="pulse-dot healthy"></span>
                <span className="mono" style={{ fontSize: '0.85rem', color: 'var(--status-success)' }}>
                  http://127.0.0.1:8000/api/v1/health/ (200 OK)
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Security & Audit Retention */}
        <div className="card">
          <div className="card-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Lock size={18} style={{ color: 'var(--status-warning)' }} />
              <span>Audit Log Retention & Security</span>
            </div>
          </div>

          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
            ReconcileOS audit logs are tamper-evident and recorded with cryptographic hashes.
            Log retention is configured for <strong>365 days</strong> with immutable event stream protection.
          </div>
        </div>
      </div>
    </div>
  );
}
