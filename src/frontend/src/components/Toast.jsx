import { useState, useEffect } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react';

let addToast;
const listeners = new Set();

export function toast(message, type = 'info') {
  const id = Date.now() + Math.random();
  listeners.forEach(fn => fn({ id, message, type }));
}

export default function Toast() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    const handler = (t) => {
      setToasts(prev => [...prev, t]);
      setTimeout(() => {
        setToasts(prev => prev.filter(x => x.id !== t.id));
      }, 4000);
    };
    listeners.add(handler);
    return () => listeners.delete(handler);
  }, []);

  const icons = {
    success: <CheckCircle size={16} className="text-noc-green" />,
    error: <XCircle size={16} className="text-noc-red" />,
    warning: <AlertTriangle size={16} className="text-noc-yellow" />,
    info: <Info size={16} className="text-noc-accent" />,
  };

  const borders = {
    success: 'border-l-noc-green',
    error: 'border-l-noc-red',
    warning: 'border-l-noc-yellow',
    info: 'border-l-noc-accent',
  };

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map(t => (
        <div
          key={t.id}
          className={`bg-noc-card border border-noc-border border-l-4 ${borders[t.type]} rounded-lg p-3 shadow-xl flex items-start gap-2 animate-slide-in`}
        >
          {icons[t.type]}
          <span className="text-sm">{t.message}</span>
          <button
            onClick={() => setToasts(prev => prev.filter(x => x.id !== t.id))}
            className="ml-auto text-noc-dim hover:text-noc-text text-xs"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}
