import React from 'react';

/**
 * Button — Primary, Secondary, Ghost / Tertiary variants.
 * Refined with pill shape directly matching the Landing Page CTA button.
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
    gap: '6px',
    borderRadius: 'var(--radius-btn)',
    fontSize: size === 'small' ? '12px' : '13px',
    fontWeight: 500,
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.5 : 1,
    transition: 'all 0.15s ease',
    border: '1px solid transparent',
    padding: size === 'small' ? '5px 12px' : '7px 16px',
    outline: 'none',
    lineHeight: 1.4,
    fontFamily: 'inherit',
    whiteSpace: 'nowrap'
  };

  let variantStyles = {};

  if (isPrimary) {
    variantStyles = {
      backgroundColor: 'var(--accent-primary)',
      color: '#FFFFFF',
      borderColor: 'var(--accent-primary)',
      boxShadow: '0 1px 2px rgba(31, 25, 44, 0.08)'
    };
  } else if (isSecondary) {
    variantStyles = {
      backgroundColor: 'var(--bg-surface)',
      color: 'var(--text-primary)',
      borderColor: 'var(--border-hairline)',
      boxShadow: '0 1px 2px rgba(31, 25, 44, 0.04)'
    };
  } else if (isDanger) {
    variantStyles = {
      backgroundColor: 'var(--status-critical)',
      color: '#FFFFFF',
      borderColor: 'var(--status-critical)',
      boxShadow: '0 1px 2px rgba(220, 38, 38, 0.15)'
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
      className={`btn ${className}`}
      {...props}
    >
      {Icon && <Icon size={size === 'small' ? 14 : 16} />}
      <span>{children}</span>
    </button>
  );
}
