import React from 'react';
import { Search, Bell, ShieldCheck, Terminal, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export function Header() {
  const { user, role, logout } = useAuth();

  return (
    <header className="header">
      <div className="header-left">
        <div className="search-wrapper">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Search employees, rules, violations..."
          />
        </div>
        <div className="env-pill">
          <Terminal size={12} />
          <span>DEV / SIMULATION</span>
        </div>
      </div>

      <div className="header-right">
        <button className="header-icon-btn" title="System Notifications">
          <Bell size={18} />
          <span className="notification-dot"></span>
        </button>

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
