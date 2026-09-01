'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught component error in ErrorBoundary:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            padding: '32px 24px',
            margin: '24px auto',
            maxWidth: 640,
            background: 'rgba(255, 75, 75, 0.08)',
            border: '1px solid rgba(255, 75, 75, 0.3)',
            borderRadius: 'var(--radius-xl, 16px)',
            backdropFilter: 'blur(16px)',
            color: '#fff',
            textAlign: 'center',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
          }}
        >
          <div style={{ fontSize: 36, marginBottom: 12 }}>🧭⚠️</div>
          <h3
            style={{
              fontFamily: 'var(--font-heading, "Playfair Display", serif)',
              fontSize: 20,
              color: '#ff7b7b',
              marginBottom: 8,
            }}
          >
            {this.props.fallbackTitle || 'A temporary visual error occurred'}
          </h3>
          <p
            style={{
              fontSize: 13.5,
              color: 'var(--text-muted, #94a3b8)',
              marginBottom: 20,
              lineHeight: 1.5,
            }}
          >
            {this.state.error?.message ||
              'The application encountered an unexpected state. Your trip data is safely preserved in local history.'}
          </p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
            <button
              type="button"
              onClick={() => this.setState({ hasError: false, error: null })}
              style={{
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: '#fff',
                padding: '8px 18px',
                borderRadius: 'var(--radius-full, 9999px)',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: 13,
              }}
            >
              Try Again
            </button>
            <button
              type="button"
              onClick={() => window.location.reload()}
              style={{
                background: 'var(--amber, #f59e0b)',
                border: 'none',
                color: '#040e1f',
                padding: '8px 18px',
                borderRadius: 'var(--radius-full, 9999px)',
                cursor: 'pointer',
                fontWeight: 700,
                fontSize: 13,
              }}
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
