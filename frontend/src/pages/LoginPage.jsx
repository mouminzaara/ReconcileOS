import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Shield, Lock, UserCheck, AlertCircle, ArrowRight, ArrowLeft } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function LoginPage() {
  const [username, setUsername] = useState('admin@reconcileos.internal');
  const [password, setPassword] = useState('admin123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'Invalid credentials. Please verify username and password.');
    } finally {
      setLoading(false);
    }
  };

  const handlePresetSelect = (presetUsername, presetPassword) => {
    setUsername(presetUsername);
    setPassword(presetPassword);
    setError(null);
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'radial-gradient(circle at 50% 30%, #EFE8DD 0%, #F5F0E8 100%)',
        padding: '20px'
      }}
    >
      <div style={{ marginBottom: '16px' }}>
        <Link
          to="/landing"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.85rem',
            fontWeight: 600,
            color: '#7865A5',
            textDecoration: 'none'
          }}
        >
          <ArrowLeft size={16} /> Back to ReconcileOS Public Site
        </Link>
      </div>

      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '460px',
          padding: '32px',
          border: '1px solid var(--border-color)',
          boxShadow: 'var(--shadow-md)',
          background: '#FFFDF9'
        }}
      >
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--accent-blue-glow)',
              border: '1px solid var(--accent-blue)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-blue)',
              margin: '0 auto 12px'
            }}
          >
            <Shield size={26} />
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-main)' }}>
            ReconcileOS Security Access
          </h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Continuous Integrity & Role-Based Access Control
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid var(--status-danger-border)',
              color: 'var(--status-danger)',
              padding: '10px 14px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.825rem',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Corporate Identity / Email
            </label>
            <input
              type="text"
              className="search-input"
              style={{ paddingLeft: '12px' }}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="user@reconcileos.internal"
              required
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Password
            </label>
            <input
              type="password"
              className="search-input"
              style={{ paddingLeft: '12px' }}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '10px', fontSize: '0.9rem' }}
            disabled={loading}
          >
            {loading ? 'Authenticating...' : 'Sign In with SimpleJWT'} <ArrowRight size={16} />
          </button>
        </form>

        {/* Quick-Fill Demo Presets */}
        <div style={{ marginTop: '28px', paddingTop: '20px', borderTop: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
            Quick-Fill Role Presets (Demonstration)
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ justifyContent: 'space-between', fontSize: '0.78rem', padding: '6px 12px' }}
              onClick={() => handlePresetSelect('admin@reconcileos.internal', 'admin123')}
            >
              <span><strong>ADMIN:</strong> admin@reconcileos.internal</span>
              <span className="badge badge-critical" style={{ fontSize: '0.65rem' }}>Full Control</span>
            </button>

            <button
              type="button"
              className="btn btn-secondary"
              style={{ justifyContent: 'space-between', fontSize: '0.78rem', padding: '6px 12px' }}
              onClick={() => handlePresetSelect('operator@reconcileos.internal', 'operator123')}
            >
              <span><strong>OPERATOR:</strong> operator@reconcileos.internal</span>
              <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>Reconcile & Plan</span>
            </button>

            <button
              type="button"
              className="btn btn-secondary"
              style={{ justifyContent: 'space-between', fontSize: '0.78rem', padding: '6px 12px' }}
              onClick={() => handlePresetSelect('viewer@reconcileos.internal', 'viewer123')}
            >
              <span><strong>VIEWER:</strong> viewer@reconcileos.internal</span>
              <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>Read Only</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
