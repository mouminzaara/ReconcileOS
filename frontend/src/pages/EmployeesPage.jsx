import React, { useState, useEffect } from 'react';
import { Search, Filter, RefreshCw, Plus, Edit2, Eye, UserX, X, Check, AlertCircle } from 'lucide-react';
import { StatusPill } from '../components/ui/StatusPill';
import { Button } from '../components/ui/Button';
import { api } from '../services/api';

export function EmployeesPage() {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [toastMessage, setToastMessage] = useState(null);

  // Modals state
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showTerminateModal, setShowTerminateModal] = useState(false);

  // Active item state
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [formData, setFormData] = useState({ full_name: '', email: '', department: '', status: 'ACTIVE' });
  const [terminateReason, setTerminateReason] = useState('');
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);

  const showToast = (text, isError = false) => {
    setToastMessage({ text, isError });
    setTimeout(() => setToastMessage(null), 4000);
  };

  const loadEmployees = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getEmployees();
      const list = res.results || res;
      if (Array.isArray(list)) {
        const formatted = list.map(emp => ({
          id: emp.id,
          fullName: emp.full_name,
          email: emp.email,
          department: emp.department,
          status: emp.status,
          createdAt: emp.created_at ? emp.created_at.split('T')[0] : '2026-08-28',
          systemsConnected: emp.systems_connected || ["HR", "VPN", "GitHub", "Cloud", "Slack"]
        }));
        setEmployees(formatted);
      } else {
        setEmployees([]);
      }
    } catch (err) {
      console.error('API error loading employees:', err);
      setError(err.message || 'Failed to load employees from HR directory.');
      setEmployees([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEmployees();
  }, []);

  const handleOpenAddModal = () => {
    setFormData({ full_name: '', email: '', department: '', status: 'ACTIVE' });
    setFormError(null);
    setShowAddModal(true);
  };

  const handleOpenEditModal = (emp) => {
    setSelectedEmployee(emp);
    setFormData({
      full_name: emp.fullName,
      email: emp.email,
      department: emp.department,
      status: emp.status
    });
    setFormError(null);
    setShowEditModal(true);
  };

  const handleOpenDetailModal = async (emp) => {
    setSelectedEmployee(emp);
    setShowDetailModal(true);
    try {
      const detail = await api.getEmployeeDetail(emp.id);
      if (detail && detail.id) {
        setSelectedEmployee(prev => ({
          ...prev,
          fullName: detail.full_name || prev.fullName,
          email: detail.email || prev.email,
          department: detail.department || prev.department,
          status: detail.status || prev.status,
          createdAt: detail.created_at ? detail.created_at.split('T')[0] : prev.createdAt
        }));
      }
    } catch {
      // Retain existing selected employee state on detail fetch fallback
    }
  };

  const handleOpenTerminateModal = (emp) => {
    setSelectedEmployee(emp);
    setTerminateReason('');
    setFormError(null);
    setShowTerminateModal(true);
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setFormSubmitting(true);
    setFormError(null);
    try {
      await api.createEmployee({
        full_name: formData.full_name,
        email: formData.email,
        department: formData.department,
        status: formData.status
      });
      showToast(`Employee "${formData.full_name}" created successfully.`);
      setShowAddModal(false);
      await loadEmployees();
    } catch (err) {
      setFormError(err.message || 'Failed to create employee');
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!selectedEmployee) return;
    setFormSubmitting(true);
    setFormError(null);
    try {
      await api.updateEmployee(selectedEmployee.id, {
        full_name: formData.full_name,
        email: formData.email,
        department: formData.department,
        status: formData.status
      });
      showToast(`Employee "${formData.full_name}" updated successfully.`);
      setShowEditModal(false);
      await loadEmployees();
    } catch (err) {
      setFormError(err.message || 'Failed to update employee');
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleTerminateSubmit = async (e) => {
    e.preventDefault();
    if (!selectedEmployee) return;
    setFormSubmitting(true);
    setFormError(null);
    try {
      await api.terminateEmployee(selectedEmployee.id, terminateReason);
      showToast(`Employee "${selectedEmployee.fullName}" terminated successfully.`);
      setShowTerminateModal(false);
      await loadEmployees();
    } catch (err) {
      setFormError(err.message || 'Failed to terminate employee');
    } finally {
      setFormSubmitting(false);
    }
  };

  const filteredEmployees = employees.filter((emp) => {
    const matchesSearch =
      (emp.fullName || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (emp.email || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (emp.department || '').toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = statusFilter === 'ALL' || emp.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="page-content">
      {/* Toast feedback banner */}
      {toastMessage && (
        <div
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            backgroundColor: toastMessage.isError ? 'var(--status-critical)' : 'var(--accent-primary)',
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
          <span>{toastMessage.text}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span>Employees</span>
          </h1>
          <p className="page-subtitle">
            Primary HR system of record — identity lifecycle directory
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button variant="secondary" icon={RefreshCw} onClick={loadEmployees} disabled={loading}>
            Refresh
          </Button>
          <Button variant="primary" icon={Plus} onClick={handleOpenAddModal}>
            Add employee
          </Button>
        </div>
      </div>

      {error && (
        <div
          style={{
            marginBottom: '20px',
            padding: '14px 18px',
            borderRadius: 'var(--radius-btn)',
            backgroundColor: 'var(--status-critical-bg)',
            border: '1px solid var(--status-critical-border)',
            color: 'var(--status-critical)',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            flexWrap: 'wrap'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
          <Button variant="secondary" size="small" icon={RefreshCw} onClick={loadEmployees} disabled={loading}>
            Retry
          </Button>
        </div>
      )}

      {/* Controls & Filters Bar */}
      <div className="card" style={{ marginBottom: '20px', padding: '16px' }}>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ position: 'relative', width: '320px' }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              className="input-base"
              style={{ width: '100%', paddingLeft: '36px' }}
              placeholder="Search name, email, department..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <Filter size={15} style={{ color: 'var(--text-muted)' }} />
            <span style={{ fontSize: '13px', color: 'var(--text-muted)', marginRight: '4px' }}>Filter:</span>
            <Button
              variant={statusFilter === 'ALL' ? 'primary' : 'secondary'}
              size="small"
              onClick={() => setStatusFilter('ALL')}
            >
              All ({employees.length})
            </Button>
            <Button
              variant={statusFilter === 'ACTIVE' ? 'primary' : 'secondary'}
              size="small"
              onClick={() => setStatusFilter('ACTIVE')}
            >
              Active ({employees.filter(e => e.status === 'ACTIVE').length})
            </Button>
            <Button
              variant={statusFilter === 'TERMINATED' ? 'primary' : 'secondary'}
              size="small"
              onClick={() => setStatusFilter('TERMINATED')}
            >
              Terminated ({employees.filter(e => e.status === 'TERMINATED').length})
            </Button>
          </div>
        </div>
      </div>

      {/* Directory Table */}
      <div className="plain-divided-container">
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
          <thead>
            <tr style={{ backgroundColor: 'var(--bg-base)', borderBottom: '1px solid var(--border-hairline)' }}>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>UUID</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Full Name</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Corporate Email</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Department</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>HR Status</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Created</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredEmployees.map((emp) => {
              const isTerminated = emp.status === 'TERMINATED';
              return (
                <tr key={emp.id} style={{ borderBottom: '1px solid var(--border-hairline)', transition: 'background-color 0.15s ease' }}>
                  <td className="font-mono" style={{ padding: '12px 16px', fontSize: '12px', color: 'var(--text-muted)' }}>
                    {emp.id.slice(0, 8)}...{emp.id.slice(-4)}
                  </td>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {emp.fullName}
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                    {emp.email}
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                    {emp.department}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <StatusPill status={isTerminated ? 'neutral' : 'healthy'} label={emp.status} size="small" />
                  </td>
                  <td className="font-mono" style={{ padding: '12px 16px', fontSize: '12px', color: 'var(--text-muted)' }}>
                    {emp.createdAt}
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '6px' }}>
                      <Button variant="tertiary" size="small" icon={Eye} onClick={() => handleOpenDetailModal(emp)}>
                        View
                      </Button>
                      <Button variant="secondary" size="small" icon={Edit2} onClick={() => handleOpenEditModal(emp)}>
                        Edit
                      </Button>
                      {!isTerminated && (
                        <Button variant="danger" size="small" icon={UserX} onClick={() => handleOpenTerminateModal(emp)}>
                          Terminate
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
            {filteredEmployees.length === 0 && (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                  {loading ? 'Loading employees...' : (employees.length === 0 ? 'No employees found in HR directory.' : 'No employees found matching the filter.')}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* --- ADD EMPLOYEE MODAL --- */}
      {showAddModal && (
        <div style={modalOverlayStyle}>
          <div style={modalContentStyle}>
            <div style={modalHeaderStyle}>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>Add New Employee</h3>
              <button style={closeBtnStyle} onClick={() => setShowAddModal(false)}><X size={18} /></button>
            </div>
            <form onSubmit={handleCreateSubmit} style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {formError && <div style={errorBannerStyle}>{formError}</div>}
              <div>
                <label style={labelStyle}>Full Name</label>
                <input
                  type="text"
                  required
                  className="input-base"
                  style={{ width: '100%' }}
                  placeholder="e.g. Sarah Connor"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                />
              </div>
              <div>
                <label style={labelStyle}>Corporate Email</label>
                <input
                  type="email"
                  required
                  className="input-base"
                  style={{ width: '100%' }}
                  placeholder="sarah.connor@reconcileos.internal"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
              <div>
                <label style={labelStyle}>Department</label>
                <input
                  type="text"
                  required
                  className="input-base"
                  style={{ width: '100%' }}
                  placeholder="e.g. Platform Security"
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
                <Button variant="secondary" type="button" onClick={() => setShowAddModal(false)}>Cancel</Button>
                <Button variant="primary" type="submit" disabled={formSubmitting}>
                  {formSubmitting ? 'Creating...' : 'Create Employee'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- EDIT EMPLOYEE MODAL --- */}
      {showEditModal && selectedEmployee && (
        <div style={modalOverlayStyle}>
          <div style={modalContentStyle}>
            <div style={modalHeaderStyle}>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>Edit Employee Record</h3>
              <button style={closeBtnStyle} onClick={() => setShowEditModal(false)}><X size={18} /></button>
            </div>
            <form onSubmit={handleEditSubmit} style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {formError && <div style={errorBannerStyle}>{formError}</div>}
              <div>
                <label style={labelStyle}>Full Name</label>
                <input
                  type="text"
                  required
                  className="input-base"
                  style={{ width: '100%' }}
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                />
              </div>
              <div>
                <label style={labelStyle}>Corporate Email</label>
                <input
                  type="email"
                  required
                  className="input-base"
                  style={{ width: '100%' }}
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
              <div>
                <label style={labelStyle}>Department</label>
                <input
                  type="text"
                  required
                  className="input-base"
                  style={{ width: '100%' }}
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
                <Button variant="secondary" type="button" onClick={() => setShowEditModal(false)}>Cancel</Button>
                <Button variant="primary" type="submit" disabled={formSubmitting}>
                  {formSubmitting ? 'Saving...' : 'Save Changes'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- EMPLOYEE DETAIL MODAL --- */}
      {showDetailModal && selectedEmployee && (
        <div style={modalOverlayStyle}>
          <div style={{ ...modalContentStyle, maxWidth: '540px' }}>
            <div style={modalHeaderStyle}>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>Employee Details</h3>
              <button style={closeBtnStyle} onClick={() => setShowDetailModal(false)}><X size={18} /></button>
            </div>
            <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h4 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>{selectedEmployee.fullName}</h4>
                  <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{selectedEmployee.email}</div>
                </div>
                <StatusPill status={selectedEmployee.status === 'TERMINATED' ? 'neutral' : 'healthy'} label={selectedEmployee.status} />
              </div>

              <div style={{ borderTop: '1px solid var(--border-hairline)', paddingTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Employee UUID:</span>
                  <span className="font-mono" style={{ color: 'var(--text-primary)' }}>{selectedEmployee.id}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Department:</span>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{selectedEmployee.department}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Created Date:</span>
                  <span className="font-mono" style={{ color: 'var(--text-primary)' }}>{selectedEmployee.createdAt}</span>
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--border-hairline)', paddingTop: '12px' }}>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Monitored Connectors
                </div>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  {(selectedEmployee.systemsConnected || ["HR", "VPN", "GitHub", "Cloud", "Slack"]).map(sys => (
                    <span key={sys} style={{ fontSize: '11px', fontWeight: 600, padding: '3px 8px', borderRadius: 'var(--radius-pill)', backgroundColor: 'var(--accent-primary-light)', color: 'var(--accent-primary)' }}>
                      {sys}
                    </span>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '12px' }}>
                <Button variant="secondary" onClick={() => setShowDetailModal(false)}>Close</Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --- TERMINATE EMPLOYEE CONFIRMATION MODAL --- */}
      {showTerminateModal && selectedEmployee && (
        <div style={modalOverlayStyle}>
          <div style={{ ...modalContentStyle, maxWidth: '480px' }}>
            <div style={modalHeaderStyle}>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--status-critical)' }}>Terminate Employee</h3>
              <button style={closeBtnStyle} onClick={() => setShowTerminateModal(false)}><X size={18} /></button>
            </div>
            <form onSubmit={handleTerminateSubmit} style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {formError && <div style={errorBannerStyle}>{formError}</div>}
              <div style={{ fontSize: '14px', color: 'var(--text-primary)', lineHeight: '1.5' }}>
                Are you sure you want to terminate <strong>{selectedEmployee.fullName}</strong> ({selectedEmployee.email})?
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                Terminating an employee marks their HR record as <code>TERMINATED</code> and triggers automated reconciliation drift checks across connected connectors (VPN, GitHub, Cloud IAM, Slack).
              </div>
              <div>
                <label style={labelStyle}>Termination Reason / Audit Note (Optional)</label>
                <input
                  type="text"
                  className="input-base"
                  style={{ width: '100%' }}
                  placeholder="e.g. End of contract / Resignation"
                  value={terminateReason}
                  onChange={(e) => setTerminateReason(e.target.value)}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
                <Button variant="secondary" type="button" onClick={() => setShowTerminateModal(false)}>Cancel</Button>
                <Button variant="danger" type="submit" disabled={formSubmitting}>
                  {formSubmitting ? 'Terminating...' : 'Terminate employee'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// Inline modal styling helpers
const modalOverlayStyle = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(36, 31, 51, 0.4)',
  backdropFilter: 'blur(4px)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 999
};

const modalContentStyle = {
  backgroundColor: 'var(--bg-surface)',
  border: '1px solid var(--border-hairline)',
  borderRadius: 'var(--radius-card)',
  width: '100%',
  maxWidth: '460px',
  boxShadow: 'var(--shadow-floating)',
  overflow: 'hidden'
};

const modalHeaderStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '16px 20px',
  borderBottom: '1px solid var(--border-hairline)',
  backgroundColor: 'var(--bg-base)'
};

const closeBtnStyle = {
  background: 'none',
  border: 'none',
  color: 'var(--text-muted)',
  cursor: 'pointer'
};

const labelStyle = {
  display: 'block',
  fontSize: '12px',
  fontWeight: 600,
  color: 'var(--text-muted)',
  marginBottom: '6px',
  textTransform: 'uppercase',
  letterSpacing: '0.05em'
};

const errorBannerStyle = {
  padding: '10px 14px',
  borderRadius: 'var(--radius-btn)',
  backgroundColor: 'var(--status-critical-bg)',
  border: '1px solid var(--status-critical-border)',
  color: 'var(--status-critical)',
  fontSize: '13px'
};
