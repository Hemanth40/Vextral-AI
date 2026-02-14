'use client';

import { useState, useEffect } from 'react';

export type ToastType = 'success' | 'error' | 'info';

interface Toast {
    id: number;
    message: string;
    type: ToastType;
}

export function useToast() {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const showToast = (message: string, type: ToastType) => {
        const id = Date.now();
        setToasts((prev) => [...prev, { id, message, type }]);
        setTimeout(() => {
            setToasts((prev) => prev.filter((t) => t.id !== id));
        }, 4000);
    };

    const ToastContainer = () => (
        <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3">
            {toasts.map((toast) => (
                <div
                    key={toast.id}
                    className={`
            px-5 py-3 rounded-lg shadow-lg text-sm font-medium transition-all duration-300 transform translate-y-0 opacity-100 flex items-center gap-3 border
            ${toast.type === 'success' ? 'bg-emerald-900/90 text-emerald-100 border-emerald-500/30' : ''}
            ${toast.type === 'error' ? 'bg-red-900/90 text-red-100 border-red-500/30' : ''}
            ${toast.type === 'info' ? 'bg-blue-900/90 text-blue-100 border-blue-500/30' : ''}
          `}
                    style={{ backdropFilter: 'blur(8px)' }}
                >
                    <span className="text-lg">
                        {toast.type === 'success' && '✅'}
                        {toast.type === 'error' && '❌'}
                        {toast.type === 'info' && 'ℹ️'}
                    </span>
                    {toast.message}
                </div>
            ))}
        </div>
    );

    return { showToast, ToastContainer };
}
