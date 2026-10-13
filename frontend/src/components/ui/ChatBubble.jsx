import React from 'react';
import { Bot, User } from 'lucide-react';

/**
 * ChatBubble — AI Rule Assistant chat message bubble.
 * Variants:
 * - 'ai' / 'system': lavender tinted surface background, dark plum text
 * - 'user': primary accent fill (#6E56CF), white text
 */
export function ChatBubble({ sender = 'ai', message, timestamp, actionTag }) {
  const isUser = sender === 'user';

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        gap: '12px',
        alignItems: 'flex-start',
        marginBottom: '16px'
      }}
    >
      <div
        style={{
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          backgroundColor: isUser ? 'var(--accent-primary)' : 'var(--accent-primary-light)',
          border: isUser ? 'none' : '1px solid var(--accent-primary-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: isUser ? '#FFFFFF' : 'var(--accent-primary)',
          flexShrink: 0
        }}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      <div style={{ maxWidth: '80%', display: 'flex', flexDirection: 'column', alignItems: isUser ? 'flex-end' : 'flex-start' }}>
        <div
          style={{
            padding: '12px 16px',
            borderRadius: isUser ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
            backgroundColor: isUser ? 'var(--accent-primary)' : 'var(--bg-surface)',
            color: isUser ? '#FFFFFF' : 'var(--text-primary)',
            border: isUser ? 'none' : '1px solid var(--border-hairline)',
            fontSize: '13px',
            lineHeight: '1.5',
            boxShadow: '0 1px 4px rgba(36, 31, 51, 0.04)'
          }}
        >
          {message}
          {actionTag && (
            <div
              style={{
                marginTop: '8px',
                padding: '4px 8px',
                borderRadius: 'var(--radius-btn)',
                backgroundColor: isUser ? 'rgba(255, 255, 255, 0.2)' : 'var(--accent-primary-light)',
                color: isUser ? '#FFFFFF' : 'var(--accent-primary)',
                fontSize: '11px',
                fontWeight: 600,
                display: 'inline-block'
              }}
            >
              {actionTag}
            </div>
          )}
        </div>

        {timestamp && (
          <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px', padding: '0 4px' }} className="font-mono">
            {timestamp}
          </span>
        )}
      </div>
    </div>
  );
}
