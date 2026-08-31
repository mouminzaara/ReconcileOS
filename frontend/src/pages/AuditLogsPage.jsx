import React, { useState } from 'react';
import { FileText, Shield, AlertTriangle, CheckCircle2, Clock, RefreshCw } from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { mockAuditLogs } from '../data/mockData';

export function AuditLogsPage() {
  const [activeTab, setActiveTab] = useState('TIMELINE');

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <FileText size={24} style={{ color: 'var(--accent-blue)' }} />
            Tamper-Evident Audit Logs
          </h1>
          <p className="page-subtitle">
            Immutable chronological audit stream capturing every phase of identity reconciliation
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className={`btn ${activeTab === 'TIMELINE' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('TIMELINE')}
          >
            Timeline Stream
          </button>
          <button
            className={`btn ${activeTab === 'TABLE' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('TABLE')}
          >
            Data Grid View
          </button>
        </div>
      </div>

      {activeTab === 'TIMELINE' ? (
        <div className="card" style={{ padding: '24px 32px' }}>
          <div style={{ position: 'relative', paddingLeft: '30px' }}>
            <div style={{
              position: 'absolute',
              top: '10px',
              bottom: '10px',
              left: '12px',
              width: '2px',
              background: 'var(--border-color)'
            }}></div>

            {mockAuditLogs.map((log) => {
              let dotBg = 'var(--accent-blue)';
              if (log.status === 'CRITICAL') dotBg = 'var(--status-danger)';
              if (log.status === 'WARNING') dotBg = 'var(--status-warning)';
              if (log.status === 'SUCCESS') dotBg = 'var(--status-success)';

              return (
                <div key={log.id} style={{ position: 'relative', marginBottom: '24px' }}>
                  <div style={{
                    position: 'absolute',
                    left: '-24px',
                    top: '4px',
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    backgroundColor: dotBg,
                    border: '3px solid var(--bg-card)',
                    boxShadow: `0 0 8px ${dotBg}`
                  }}></div>

                  <div style={{
                    background: 'var(--bg-card-secondary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '14px 18px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span className="mono" style={{ color: 'var(--accent-blue)', fontWeight: 700, fontSize: '0.8rem' }}>
                          {log.id}
                        </span>
                        <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
                          {log.eventType}
                        </span>
                        <span className="badge badge-info" style={{ fontSize: '0.7rem', background: '#D8CDEA', color: '#332F3A' }}>
                          {log.system}
                        </span>
                      </div>
                      <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {log.timestamp}
                      </span>
                    </div>

                    <div style={{ fontSize: '0.9rem', color: 'var(--text-main)', marginBottom: '4px' }}>
                      {log.details}
                    </div>

                    <div style={{ display: 'flex', gap: '16px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      <span>Actor: <strong style={{ color: 'var(--text-secondary)' }}>{log.actor}</strong></span>
                      <span>Target: <strong style={{ color: 'var(--text-secondary)' }}>{log.target}</strong></span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Log ID</th>
                <th>Timestamp</th>
                <th>Event Type</th>
                <th>Actor</th>
                <th>Target Identity</th>
                <th>System</th>
                <th>Event Summary</th>
                <th>Outcome</th>
              </tr>
            </thead>
            <tbody>
              {mockAuditLogs.map((log) => (
                <tr key={log.id}>
                  <td className="mono" style={{ color: 'var(--accent-blue)', fontWeight: 600 }}>
                    {log.id}
                  </td>
                  <td className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {log.timestamp}
                  </td>
                  <td>
                    <span className="badge badge-info" style={{ fontSize: '0.68rem' }}>
                      {log.eventType}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.8rem' }}>{log.actor}</td>
                  <td style={{ fontSize: '0.8rem' }}>{log.target}</td>
                  <td>
                    <span className="badge badge-info" style={{ fontSize: '0.68rem' }}>{log.system}</span>
                  </td>
                  <td style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                    {log.details}
                  </td>
                  <td>
                    <StatusBadge status={log.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
