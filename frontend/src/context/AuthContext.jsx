import React, { createContext, useContext, useState, useEffect } from 'react';
import { api, getStoredToken, clearStoredTokens } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const token = getStoredToken();
    if (!token) {
      clearStoredTokens();
      return null;
    }
    const cached = localStorage.getItem('reconcileos_user');
    if (!cached) return null;
    try {
      return JSON.parse(cached);
    } catch {
      clearStoredTokens();
      return null;
    }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getStoredToken();
    if (token) {
      api.getMe()
        .then(u => {
          setUser(u);
          localStorage.setItem('reconcileos_user', JSON.stringify(u));
        })
        .catch(err => {
          console.warn('Session expired or invalid token:', err);
          clearStoredTokens();
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      clearStoredTokens();
      setUser(null);
      setLoading(false);
    }

    const handleUnauthorized = () => {
      clearStoredTokens();
      setUser(null);
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  const login = async (username, password) => {
    const res = await api.login(username, password);
    setUser(res.user);
    return res.user;
  };

  const logout = () => {
    clearStoredTokens();
    api.logout();
    setUser(null);
  };

  const hasValidAuth = Boolean(user && getStoredToken());

  const value = {
    user,
    role: user?.role || 'GUEST',
    isAuthenticated: hasValidAuth,
    isAdmin: hasValidAuth && (user?.role === 'ADMIN' || user?.is_superuser),
    isOperator: hasValidAuth && (user?.role === 'ADMIN' || user?.role === 'OPERATOR' || user?.is_superuser),
    isViewer: hasValidAuth,
    loading,
    login,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
