import React from 'react';

/**
 * Button — Primary, Secondary, Ghost / Tertiary variants.
 * Ensures consistent labeling, 8px radius, and visible focus rings.
 */
export function Button({
  children,
  variant = 'primary',
  size = 'medium',
  icon: Icon,
  disabled = false,
  onClick,
  type = 'button',
  style = {},
  className = '',
  ...props
}) {
  const isPrimary = variant === 'primary';
  const isSecondary = variant === 'secondary';
  const isDanger = variant === 'danger';
  const isGhost = variant === 'ghost' || variant === 'tertiary';

  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    borderRadius: 'var(--radius-btn)',
    fontSize: size === 'small' ? '12px' : '14px',
    fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.6 : 1,
    transition: 'all 0.15s ease',
    border: '1px solid transparent',
    padding: size === 'small' ? '6px 12px' : '8px 16px',
    outline: 'none',
    lineHeight: 1.4,
    fontFamily: 'inherit'
  };

  let variantStyles = {};

  if (isPrimary) {
    variantStyles = {
      backgroundColor: 'var(--accent-primary)',
      color: '#FFFFFF',
      borderColor: 'var(--accent-primary)'
    };
  } else if (isSecondary) {
    variantStyles = {
      backgroundColor: 'var(--bg-surface)',
      color: 'var(--text-primary)',
      borderColor: 'var(--border-hairline)'
    };
  } else if (isDanger) {
    variantStyles = {
      backgroundColor: 'var(--status-critical)',
      color: '#FFFFFF',
      borderColor: 'var(--status-critical)'
    };
  } else if (isGhost) {
    variantStyles = {
      backgroundColor: 'transparent',
      color: 'var(--text-secondary)',
      borderColor: 'transparent'
    };
  }

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      style={{
        ...baseStyles,
        ...variantStyles,
        ...style
      }}
      className={`btn-primitive ${className}`}
      {...props}
    >
      {Icon && <Icon size={size === 'small' ? 14 : 16} />}
      <span>{children}</span>
    </button>
  );
}
