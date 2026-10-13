import React, { useState, useEffect, useRef } from 'react';
import { Search, Bell, ShieldCheck, Terminal, LogOut, X, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export function Header() {
  const { user, role, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [showNotifications, setShowNotifications] = useState(false);
  const popoverRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target)) {
        setShowNotifications(false);
      }
    };
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setShowNotifications(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  return (
    <header className="header">
      <div className="header-left">
        <div className="search-wrapper" style={{ position: 'relative' }}>
          <Search size={16} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Quick search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            title="Local header search filter"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              style={{
                position: 'absolute',
                right: '10px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                padding: 0
              }}
              title="Clear search"
            >
              <X size={14} />
            </button>
          )}
        </div>
        <div className="env-pill">
          <Terminal size={12} />
          <span>DEV / SIMULATION</span>
        </div>
      </div>

      <div className="header-right">
        <div ref={popoverRef} style={{ position: 'relative' }}>
          <button
            className="header-icon-btn"
            title="System Notifications"
            onClick={() => setShowNotifications((prev) => !prev)}
            aria-expanded={showNotifications}
          >
            <Bell size={18} />
            <span className="notification-dot"></span>
          </button>

          {showNotifications && (
            <div
              style={{
                position: 'absolute',
                right: 0,
                top: '40px',
                width: '320px',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-hairline)',
                borderRadius: 'var(--radius-card)',
                boxShadow: 'var(--shadow-floating)',
                zIndex: 1000,
                padding: '16px'
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '12px',
                  borderBottom: '1px solid var(--border-hairline)',
                  paddingBottom: '8px'
                }}
              >
                <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  System Notifications
                </span>
                <button
                  onClick={() => setShowNotifications(false)}
                  style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                >
                  <X size={14} />
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start', fontSize: '12px' }}>
                  <CheckCircle2 size={16} style={{ color: 'var(--status-healthy)', flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Integrity Daemon Active</div>
                    <div style={{ color: 'var(--text-muted)' }}>Continuous monitoring scan frequency: Every 5 mins.</div>
                  </div>
                </div>

                <div
                  style={{
                    fontSize: '11px',
                    color: 'var(--text-muted)',
                    textAlign: 'center',
                    paddingTop: '8px',
                    borderTop: '1px solid var(--border-hairline)'
                  }}
                >
                  No new unread security alerts.
                </div>
              </div>
            </div>
          )}
        </div>

        {user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div className="user-profile-chip">
              <div className="user-avatar">
                <ShieldCheck size={16} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span className="user-name">{user.email || user.username}</span>
                <span
                  className="mono"
                  style={{
                    fontSize: '0.65rem',
                    color: role === 'ADMIN' ? 'var(--status-danger)' : role === 'OPERATOR' ? 'var(--status-warning)' : 'var(--accent-blue)',
                    fontWeight: 700
                  }}
                >
                  ROLE: {role}
                </span>
              </div>
            </div>

            <button
              className="btn btn-secondary"
              style={{ padding: '6px 10px', fontSize: '0.75rem' }}
              onClick={logout}
              title="Sign Out"
            >
              <LogOut size={14} /> Logout
            </button>
          </div>
        ) : (
          <div className="user-profile-chip">
            <span className="user-name">Guest</span>
          </div>
        )}
      </div>
    </header>
  );
}

