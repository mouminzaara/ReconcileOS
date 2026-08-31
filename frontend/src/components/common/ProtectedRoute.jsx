import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ShieldAlert, Lock } from 'lucide-react';

export function ProtectedRoute({ children, allowedRoles = [] }) {
  const { user, role, isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <div className="mono" style={{ color: 'var(--text-muted)' }}>Loading authentication session...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(role) && !user?.is_superuser) {
    return (
      <div style={{ padding: '40px 20px', maxWidth: '800px', margin: '0 auto' }}>
        <div
          className="card"
          style={{
            borderColor: 'var(--status-danger-border)',
            background: 'rgba(239, 68, 68, 0.06)',
            textAlign: 'center',
            padding: '40px 24px'
          }}
        >
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.15)',
              color: 'var(--status-danger)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px'
            }}
          >
            <Lock size={28} />
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '8px' }}>
            403 Access Denied: Privileged Role Required
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '20px', lineHeight: '1.5' }}>
            Your account <strong className="mono">{user?.email}</strong> is assigned the <span className="badge badge-info">{role}</span> role.
            Access to this operational area requires one of the following roles: {allowedRoles.join(', ')}.
          </p>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Backend API security strictly enforces Role-Based Access Control (RBAC) at the server layer.
          </div>
        </div>
      </div>
    );
  }

  return children;
}
