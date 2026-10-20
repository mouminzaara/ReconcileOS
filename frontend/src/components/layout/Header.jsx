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
      {/* Left: Understated Quick Search */}
      <div className="header-left">
        <div className="header-search-wrapper">
          <Search size={14} className="header-search-icon" />
          <input
            type="text"
            className="header-search-input"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            title="Search"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="header-search-clear"
              title="Clear search"
            >
              <X size={13} />
            </button>
          )}
        </div>

        {/* Subtle Environment Indicator */}
        <div className="header-env-indicator">
          <Terminal size={12} className="header-env-icon" />
          <span>DEV / SIMULATION</span>
        </div>
      </div>

      {/* Right: Notifications, User Identity & Quiet Logout */}
      <div className="header-right">
        {/* Notification Button */}
        <div ref={popoverRef} style={{ position: 'relative' }}>
          <button
            className="header-notification-btn"
            title="System Notifications"
            onClick={() => setShowNotifications((prev) => !prev)}
            aria-expanded={showNotifications}
          >
            <Bell size={17} />
            <span className="header-notification-dot" />
          </button>

          {showNotifications && (
            <div className="header-notification-popover">
              <div className="header-popover-header">
                <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  System Notifications
                </span>
                <button
                  onClick={() => setShowNotifications(false)}
                  style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '2px' }}
                >
                  <X size={14} />
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start', fontSize: '12px' }}>
                  <CheckCircle2 size={16} style={{ color: 'var(--status-healthy)', flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Integrity Daemon Active</div>
                    <div style={{ color: 'var(--text-muted)', marginTop: '2px' }}>Continuous monitoring cadence: Every 5 mins.</div>
                  </div>
                </div>

                <div
                  style={{
                    fontSize: '11px',
                    color: 'var(--text-muted)',
                    textAlign: 'center',
                    paddingTop: '10px',
                    borderTop: '1px solid var(--border-hairline)'
                  }}
                >
                  No unread critical alerts.
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="header-divider" />

        {/* User Identity & Logout */}
        {user ? (
          <div className="header-user-section">
            <div className="header-identity-group">
              <div className="header-identity-avatar">
                <ShieldCheck size={15} />
              </div>
              <div className="header-identity-text">
                <span className="header-identity-email">{user.email || user.username}</span>
                <span
                  className="header-identity-role"
                  style={{
                    color: role === 'ADMIN' ? 'var(--status-critical)' : role === 'OPERATOR' ? 'var(--status-warning)' : 'var(--accent-primary)'
                  }}
                >
                  ROLE: {role}
                </span>
              </div>
            </div>

            <button
              className="header-logout-btn"
              onClick={logout}
              title="Sign Out"
            >
              <span>Logout</span>
              <LogOut size={13} className="header-logout-icon" />
            </button>
          </div>
        ) : (
          <div className="header-identity-text">
            <span className="header-identity-email">Guest</span>
          </div>
        )}
      </div>
    </header>
  );
}

