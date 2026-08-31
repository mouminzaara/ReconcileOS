import React from 'react';
import { Server, Users, Shield, GitBranch, Cloud, MessageSquare, RefreshCw } from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { mockConnectedSystems } from '../data/mockData';

const iconMap = {
  Users: Users,
  ShieldAlert: Shield,
  GitBranch: GitBranch,
  Cloud: Cloud,
  MessageSquare: MessageSquare
};

export function ConnectedSystemsPage() {
  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Server size={24} style={{ color: 'var(--accent-blue)' }} />
            Connected Connector Integrations
          </h1>
          <p className="page-subtitle">
            Monitored system gateways and state telemetry connectors
          </p>
        </div>
        <button className="btn btn-secondary" onClick={() => alert('Testing connection to all gateways...')}>
          <RefreshCw size={14} /> Test All Connectors
        </button>
      </div>

      <div className="grid-3">
        {mockConnectedSystems.map((sys) => {
          const Icon = iconMap[sys.icon] || Server;
          const isDrift = sys.status === 'DRIFT_DETECTED';

          return (
            <div key={sys.id} className="card system-card">
              <div>
                <div className="system-card-header">
                  <div className="system-info">
                    <div className="system-icon">
                      <Icon size={22} />
                    </div>
                    <div>
                      <div className="system-title">{sys.name}</div>
                      <div className="system-type">{sys.type}</div>
                    </div>
                  </div>
                  <span className={`pulse-dot ${isDrift ? 'drift' : 'healthy'}`}></span>
                </div>

                <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: '1.4' }}>
                  {sys.description}
                </p>
              </div>

              <div className="system-details">
                <div className="detail-row">
                  <span className="detail-label">Connection Status</span>
                  <StatusBadge status={sys.status} />
                </div>
                <div className="detail-row">
                  <span className="detail-label">System Type</span>
                  <span className="detail-val">{sys.type}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Protocol / Engine</span>
                  <span className="mono detail-val">{sys.protocol}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Last Telemetry Check</span>
                  <span className="detail-val">{sys.lastChecked}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Response Latency</span>
                  <span className="mono detail-val">{sys.latency}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Monitored Identies</span>
                  <span className="mono detail-val" style={{ color: 'var(--accent-blue)', fontWeight: 600 }}>
                    {sys.activeAccounts} accounts
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
