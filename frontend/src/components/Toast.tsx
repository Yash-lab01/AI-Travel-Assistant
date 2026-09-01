'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export type ToastType = 'success' | 'info' | 'warning' | 'error';

export interface ToastMessage {
  id: string;
  title?: string;
  message: string;
  type: ToastType;
  icon?: string;
  duration?: number;
}

interface ToastContextType {
  showToast: (toast: Omit<ToastMessage, 'id'>) => void;
  success: (message: string, title?: string) => void;
  info: (message: string, title?: string) => void;
  warning: (message: string, title?: string) => void;
  error: (message: string, title?: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

const TOAST_ICONS: Record<ToastType, string> = {
  success: '✨',
  info: '💡',
  warning: '⚠️',
  error: '❌',
};

const TOAST_ACCENTS: Record<ToastType, { border: string; glow: string; text: string }> = {
  success: { border: 'rgba(34, 197, 94, 0.4)', glow: 'rgba(34, 197, 94, 0.15)', text: '#4ade80' },
  info: { border: 'rgba(0, 219, 231, 0.4)', glow: 'rgba(0, 219, 231, 0.15)', text: '#00DBE7' },
  warning: { border: 'rgba(245, 158, 11, 0.4)', glow: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24' },
  error: { border: 'rgba(239, 68, 68, 0.4)', glow: 'rgba(239, 68, 68, 0.15)', text: '#f87171' },
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    ({ title, message, type = 'info', icon, duration = 3500 }: Omit<ToastMessage, 'id'>) => {
      const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const newToast: ToastMessage = { id, title, message, type, icon, duration };

      setToasts((prev) => [...prev.slice(-4), newToast]); // max 5 toasts visible

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  const success = useCallback((message: string, title?: string) => showToast({ message, title, type: 'success' }), [showToast]);
  const info = useCallback((message: string, title?: string) => showToast({ message, title, type: 'info' }), [showToast]);
  const warning = useCallback((message: string, title?: string) => showToast({ message, title, type: 'warning' }), [showToast]);
  const error = useCallback((message: string, title?: string) => showToast({ message, title, type: 'error' }), [showToast]);

  return (
    <ToastContext.Provider value={{ showToast, success, info, warning, error }}>
      {children}
      {/* Toast Container */}
      <div
        className="toast-viewport"
        style={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
          pointerEvents: 'none',
          maxWidth: 'calc(100vw - 48px)',
          width: 360,
        }}
      >
        {toasts.map((toast) => {
          const accent = TOAST_ACCENTS[toast.type];
          const icon = toast.icon || TOAST_ICONS[toast.type];

          return (
            <div
              key={toast.id}
              className="toast-card-animate"
              style={{
                pointerEvents: 'auto',
                background: 'rgba(6, 18, 38, 0.88)',
                backdropFilter: 'blur(20px)',
                WebkitBackdropFilter: 'blur(20px)',
                border: `1px solid ${accent.border}`,
                boxShadow: `0 12px 36px rgba(0, 0, 0, 0.5), 0 0 20px ${accent.glow}`,
                borderRadius: 'var(--radius-lg, 16px)',
                padding: '12px 16px',
                color: '#fff',
                display: 'flex',
                alignItems: 'flex-start',
                gap: 12,
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  fontSize: 18,
                  lineHeight: 1,
                  padding: 6,
                  borderRadius: 'var(--radius-md, 12px)',
                  background: accent.glow,
                  flexShrink: 0,
                }}
              >
                {icon}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                {toast.title && (
                  <div
                    style={{
                      fontFamily: 'var(--font-label, sans-serif)',
                      fontSize: 12.5,
                      fontWeight: 700,
                      color: accent.text,
                      marginBottom: 2,
                    }}
                  >
                    {toast.title}
                  </div>
                )}
                <div
                  style={{
                    fontFamily: 'var(--font-body, sans-serif)',
                    fontSize: 13,
                    color: 'var(--text-secondary, #cbd5e1)',
                    lineHeight: 1.4,
                  }}
                >
                  {toast.message}
                </div>
              </div>
              <button
                type="button"
                onClick={() => removeToast(toast.id)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted, #64748b)',
                  cursor: 'pointer',
                  fontSize: 14,
                  padding: '2px 4px',
                  borderRadius: 4,
                  lineHeight: 1,
                }}
              >
                ✕
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    // Return safe fallback if used outside provider
    return {
      showToast: () => {},
      success: (msg: string) => console.log('[Toast Success]:', msg),
      info: (msg: string) => console.log('[Toast Info]:', msg),
      warning: (msg: string) => console.warn('[Toast Warning]:', msg),
      error: (msg: string) => console.error('[Toast Error]:', msg),
    };
  }
  return context;
}
