import React, { useState, useEffect } from 'react';
import { Users, Search, Filter, RefreshCw } from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { api } from '../services/api';
import { mockEmployees } from '../data/mockData';

export function EmployeesPage() {
  const [employees, setEmployees] = useState(mockEmployees);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const loadEmployees = async () => {
    setLoading(true);
    try {
      const res = await api.getEmployees();
      const list = res.results || res;
      if (Array.isArray(list) && list.length > 0) {
        const formatted = list.map(emp => ({
          id: emp.id,
          fullName: emp.full_name,
          email: emp.email,
          department: emp.department,
          status: emp.status,
          createdAt: emp.created_at ? emp.created_at.split('T')[0] : '2026-08-28',
          systemsConnected: ["HR", "VPN", "GitHub", "Cloud", "Slack"]
        }));
        setEmployees(formatted);
      }
    } catch (err) {
      console.warn('API error loading employees, using mock data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEmployees();
  }, []);

  const filteredEmployees = employees.filter((emp) => {
    const matchesSearch =
      (emp.fullName || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (emp.email || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (emp.department || '').toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = statusFilter === 'ALL' || emp.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Users size={24} style={{ color: 'var(--accent-blue)' }} />
            HR System of Record - Employee Directory
          </h1>
          <p className="page-subtitle">
            Primary identity directory monitored continuously for lifecycle state transitions
          </p>
        </div>
        <button className="btn btn-secondary" onClick={loadEmployees} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>

      <div className="card" style={{ marginBottom: '20px', padding: '16px' }}>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="search-wrapper" style={{ width: '320px' }}>
            <Search size={16} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search by name, email, department..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <Filter size={16} style={{ color: 'var(--text-muted)' }} />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Status:</span>
            <button
              className={`btn ${statusFilter === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '4px 12px', fontSize: '0.75rem' }}
              onClick={() => setStatusFilter('ALL')}
            >
              All ({employees.length})
            </button>
            <button
              className={`btn ${statusFilter === 'ACTIVE' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '4px 12px', fontSize: '0.75rem' }}
              onClick={() => setStatusFilter('ACTIVE')}
            >
              Active ({employees.filter(e => e.status === 'ACTIVE').length})
            </button>
            <button
              className={`btn ${statusFilter === 'TERMINATED' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '4px 12px', fontSize: '0.75rem' }}
              onClick={() => setStatusFilter('TERMINATED')}
            >
              Terminated ({employees.filter(e => e.status === 'TERMINATED').length})
            </button>
          </div>
        </div>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Employee ID (UUID)</th>
              <th>Full Name</th>
              <th>Corporate Email</th>
              <th>Department</th>
              <th>HR Status</th>
              <th>Connected Downstreams</th>
              <th>Created Date</th>
            </tr>
          </thead>
          <tbody>
            {filteredEmployees.map((emp) => (
              <tr key={emp.id}>
                <td className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {emp.id.slice(0, 8)}...{emp.id.slice(-4)}
                </td>
                <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                  {emp.fullName}
                </td>
                <td style={{ color: 'var(--text-secondary)' }}>
                  {emp.email}
                </td>
                <td>
                  <span className="mono" style={{ fontSize: '0.8rem' }}>{emp.department}</span>
                </td>
                <td>
                  <StatusBadge status={emp.status} />
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                    {(emp.systemsConnected || ["HR", "VPN", "GitHub", "Cloud", "Slack"]).map((sys) => (
                      <span key={sys} className="badge badge-info" style={{ fontSize: '0.65rem', padding: '2px 6px' }}>
                        {sys}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {emp.createdAt}
                </td>
              </tr>
            ))}
            {filteredEmployees.length === 0 && (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                  No employee records matched your filter query.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
