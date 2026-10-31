import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Bell,
  ShieldCheck,
  Terminal,
  LogOut,
  X,
  CheckCircle2,
  Users,
  ShieldAlert,
  Activity,
  FileText,
  Loader2
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { StatusPill } from '../ui/StatusPill';
import { getSearchDataset, executeSearch } from '../../services/search';

export function Header() {
  const { user, role, logout } = useAuth();
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [searchResults, setSearchResults] = useState({
    employees: [],
    violations: [],
    repairs: [],
    auditLogs: [],
    totalCount: 0,
    rawCounts: {}
  });
  const [selectedIndex, setSelectedIndex] = useState(-1);

  const [showNotifications, setShowNotifications] = useState(false);
  const popoverRef = useRef(null);
  const searchWrapperRef = useRef(null);
  const inputRef = useRef(null);

  // Debounce search query input (200ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery.trim());
    }, 200);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Execute search when debounced query updates
  useEffect(() => {
    if (!debouncedQuery) {
      return;
    }

    let isCancelled = false;
    setSearchLoading(true);
    setSearchError(null);

    getSearchDataset()
      .then((dataset) => {
        if (!isCancelled) {
          const res = executeSearch(dataset, debouncedQuery);
          setSearchResults(res);
          setSelectedIndex(-1);
        }
      })
      .catch(() => {
        if (!isCancelled) {
          setSearchError('Search failed to load records. Please retry.');
        }
      })
      .finally(() => {
        if (!isCancelled) {
          setSearchLoading(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [debouncedQuery]);

  // Click outside and global Escape key listener
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target)) {
        setShowNotifications(false);
      }
      if (searchWrapperRef.current && !searchWrapperRef.current.contains(e.target)) {
        setIsSearchOpen(false);
      }
    };
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setShowNotifications(false);
        setIsSearchOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const flattenedResults = [
    ...(searchResults.employees || []),
    ...(searchResults.violations || []),
    ...(searchResults.repairs || []),
    ...(searchResults.auditLogs || []),
  ];

  const handleSelectResult = (item) => {
    setIsSearchOpen(false);
    setSelectedIndex(-1);
    navigate(item.url);
  };

  const handleSearchKeyDown = (e) => {
    if (!isSearchOpen && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
      if (searchQuery.trim()) {
        setIsSearchOpen(true);
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (flattenedResults.length > 0) {
        setSelectedIndex((prev) => (prev + 1) % flattenedResults.length);
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (flattenedResults.length > 0) {
        setSelectedIndex((prev) => (prev <= 0 ? flattenedResults.length - 1 : prev - 1));
      }
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0 && flattenedResults[selectedIndex]) {
        handleSelectResult(flattenedResults[selectedIndex]);
      } else if (searchQuery.trim()) {
        navigate(`/employees?search=${encodeURIComponent(searchQuery.trim())}`);
        setIsSearchOpen(false);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setIsSearchOpen(false);
      setSelectedIndex(-1);
    }
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setDebouncedQuery('');
    setIsSearchOpen(false);
    setSelectedIndex(-1);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  // Helper to calculate running index for keyboard selection
  let currentGroupOffset = 0;

  return (
    <header className="header">
      {/* Left: Functional Quick Search with Dropdown */}
      <div className="header-left">
        <div className="header-search-wrapper" ref={searchWrapperRef}>
          <Search size={14} className="header-search-icon" aria-hidden="true" />
          <input
            ref={inputRef}
            type="text"
            className="header-search-input"
            placeholder="Search records, IDs, emails..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              if (!isSearchOpen) setIsSearchOpen(true);
            }}
            onFocus={() => {
              if (searchQuery.trim()) setIsSearchOpen(true);
            }}
            onKeyDown={handleSearchKeyDown}
            role="combobox"
            aria-autocomplete="list"
            aria-expanded={isSearchOpen}
            aria-controls="header-search-results"
            aria-label="Global application search"
          />
          {searchQuery && (
            <button
              onClick={handleClearSearch}
              className="header-search-clear"
              title="Clear search"
              aria-label="Clear search query"
            >
              <X size={13} />
            </button>
          )}

          {/* Results Dropdown */}
          {isSearchOpen && debouncedQuery && (
            <div className="header-search-dropdown" id="header-search-results" role="listbox">
              {searchLoading ? (
                <div className="header-search-loading">
                  <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
                  <span>Searching directory and records...</span>
                </div>
              ) : searchError ? (
                <div className="header-search-empty">
                  {searchError}
                </div>
              ) : searchResults.totalCount === 0 ? (
                <div className="header-search-empty">
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    No records found for "{debouncedQuery}"
                  </div>
                  <div style={{ fontSize: '11.5px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Try searching by employee name, email, system, rule code, or record ID.
                  </div>
                </div>
              ) : (
                <>
                  <div className="header-search-results-list">
                    {/* Category: Employees */}
                    {searchResults.employees.length > 0 && (
                      <div className="header-search-group">
                        <div className="header-search-group-header">
                          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Users size={12} />
                            <span>Employees ({searchResults.rawCounts.employees})</span>
                          </span>
                        </div>
                        {searchResults.employees.map((item) => {
                          const itemIndex = currentGroupOffset++;
                          const isSelected = selectedIndex === itemIndex;
                          return (
                            <button
                              key={item.id}
                              type="button"
                              className={`header-search-item ${isSelected ? 'is-selected' : ''}`}
                              onClick={() => handleSelectResult(item)}
                              role="option"
                              aria-selected={isSelected}
                            >
                              <div className="header-search-item-info">
                                <div className="header-search-item-title">{item.title}</div>
                                <div className="header-search-item-sub">{item.subtitle}</div>
                              </div>
                              <div className="header-search-item-badge">
                                <StatusPill status={item.statusVariant} label={item.status} size="small" />
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}

                    {/* Category: Violations */}
                    {searchResults.violations.length > 0 && (
                      <div className="header-search-group">
                        <div className="header-search-group-header">
                          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <ShieldAlert size={12} />
                            <span>Violations ({searchResults.rawCounts.violations})</span>
                          </span>
                        </div>
                        {searchResults.violations.map((item) => {
                          const itemIndex = currentGroupOffset++;
                          const isSelected = selectedIndex === itemIndex;
                          return (
                            <button
                              key={item.id}
                              type="button"
                              className={`header-search-item ${isSelected ? 'is-selected' : ''}`}
                              onClick={() => handleSelectResult(item)}
                              role="option"
                              aria-selected={isSelected}
                            >
                              <div className="header-search-item-info">
                                <div className="header-search-item-title">{item.title}</div>
                                <div className="header-search-item-sub">{item.subtitle}</div>
                              </div>
                              <div className="header-search-item-badge">
                                <StatusPill status={item.statusVariant} label={item.status} size="small" />
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}

                    {/* Category: Repair Plans */}
                    {searchResults.repairs.length > 0 && (
                      <div className="header-search-group">
                        <div className="header-search-group-header">
                          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Activity size={12} />
                            <span>Repair Plans ({searchResults.rawCounts.repairs})</span>
                          </span>
                        </div>
                        {searchResults.repairs.map((item) => {
                          const itemIndex = currentGroupOffset++;
                          const isSelected = selectedIndex === itemIndex;
                          return (
                            <button
                              key={item.id}
                              type="button"
                              className={`header-search-item ${isSelected ? 'is-selected' : ''}`}
                              onClick={() => handleSelectResult(item)}
                              role="option"
                              aria-selected={isSelected}
                            >
                              <div className="header-search-item-info">
                                <div className="header-search-item-title">{item.title}</div>
                                <div className="header-search-item-sub">{item.subtitle}</div>
                              </div>
                              <div className="header-search-item-badge">
                                <StatusPill status={item.statusVariant} label={item.status} size="small" />
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}

                    {/* Category: Audit Events */}
                    {searchResults.auditLogs.length > 0 && (
                      <div className="header-search-group">
                        <div className="header-search-group-header">
                          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <FileText size={12} />
                            <span>Audit Events ({searchResults.rawCounts.auditLogs})</span>
                          </span>
                        </div>
                        {searchResults.auditLogs.map((item) => {
                          const itemIndex = currentGroupOffset++;
                          const isSelected = selectedIndex === itemIndex;
                          return (
                            <button
                              key={item.id}
                              type="button"
                              className={`header-search-item ${isSelected ? 'is-selected' : ''}`}
                              onClick={() => handleSelectResult(item)}
                              role="option"
                              aria-selected={isSelected}
                            >
                              <div className="header-search-item-info">
                                <div className="header-search-item-title">{item.title}</div>
                                <div className="header-search-item-sub">{item.subtitle}</div>
                              </div>
                              <div className="header-search-item-badge">
                                <StatusPill status={item.statusVariant} label={item.status} size="small" />
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  <div className="header-search-footer">
                    <span>{searchResults.totalCount} matching record{searchResults.totalCount === 1 ? '' : 's'}</span>
                    <span>↑↓ Navigate • ↵ Select • Esc Close</span>
                  </div>
                </>
              )}
            </div>
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

