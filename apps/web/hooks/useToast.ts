/**
 * useToast Hook
 *
 * Simple toast notification hook for displaying temporary messages.
 * This is a basic implementation that can be replaced with a more robust solution.
 */

'use client';

import { useState, useCallback } from 'react';

export interface Toast {
  title: string;
  description?: string;
  variant?: 'default' | 'destructive';
}

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((toast: Toast) => {
    setToasts((prev) => [...prev, toast]);

    // Auto-dismiss after 3 seconds
    setTimeout(() => {
      setToasts((prev) => prev.slice(1));
    }, 3000);

    // Log to console for now
    console.log(`[Toast ${toast.variant ?? 'default'}]`, toast.title, toast.description);
  }, []);

  return { toast, toasts };
}
