'use client';

import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import styled from 'styled-components';

type Toast = { id: string; message: string };

type ToastContextValue = {
  toast: (message: string) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export const useToast = () => {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
};

export const ToastProvider = ({ children }: { children: React.ReactNode }) => {
  const [items, setItems] = useState<Toast[]>([]);

  const toast = useCallback((message: string) => {
    const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    setItems((prev) => [...prev, { id, message }]);

    window.setTimeout(() => {
      setItems((prev) => prev.filter((t) => t.id !== id));
    }, 2200);
  }, []);

  const value = useMemo(() => ({ toast }), [toast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <Wrap aria-live="polite" aria-relevant="additions">
        {items.map((t) => (
          <ToastItem key={t.id}>{t.message}</ToastItem>
        ))}
      </Wrap>
    </ToastContext.Provider>
  );
};

const Wrap = styled.div`
  position: fixed;
  left: 50%;
  bottom: 76px;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: min(520px, calc(100vw - 24px));
  pointer-events: none;
`;

const ToastItem = styled.div`
  background: rgba(31, 31, 31, 0.92);
  color: #fff;
  border-radius: 999px;
  padding: 10px 14px;
  font-size: 14px;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0,0,0,.18);
`;
