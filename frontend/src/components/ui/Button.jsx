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
    gap: '8px',
    borderRadius: 'var(--radius-btn)',
    fontSize: size === 'small' ? '12.5px' : '13.5px',
    fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.55 : 1,
    transition: 'all 0.2s ease',
    border: '1px solid transparent',
    padding: size === 'small' ? '6px 14px' : '9px 20px',
    outline: 'none',
    lineHeight: 1.4,
    fontFamily: 'inherit',
    whiteSpace: 'nowrap'
  };

  let variantStyles = {};

  if (isPrimary) {
    variantStyles = {
      backgroundColor: 'var(--accent-primary)',
      color: '#FFFDF9',
      borderColor: 'var(--accent-primary)',
      boxShadow: '0 2px 10px rgba(120, 101, 165, 0.25)'
    };
  } else if (isSecondary) {
    variantStyles = {
      backgroundColor: 'var(--bg-surface)',
      color: 'var(--text-primary)',
      borderColor: 'var(--border-hairline)',
      boxShadow: '0 1px 4px rgba(51, 47, 58, 0.04)'
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
      className={`btn ${className}`}
      {...props}
    >
      {Icon && <Icon size={size === 'small' ? 14 : 16} />}
      <span>{children}</span>
    </button>
  );
}
