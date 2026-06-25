import { useState } from 'react';
import api from '../api';

export default function TargetForm({ target, onClose, onSaved }) {
  const isEdit = !!target;
  const [form, setForm] = useState({
    name: target?.name || '',
    ip: target?.ip || '',
    interval: target?.interval || 60,
    ping_count: target?.ping_count || 4,
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isEdit) {
        await api.put(`/targets/${target.id}`, form);
      } else {
        await api.post('/targets', form);
      }
      onSaved?.();
    } catch (err) {
      setError(err.response?.data?.detail || 'Operation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div className="card w-full max-w-md mx-4" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-semibold mb-4">
          {isEdit ? 'Edit Target' : 'Add Target'}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="text-sm text-noc-muted mb-1 block">Name</label>
            <input
              type="text"
              className="input-field"
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. Google DNS"
              required
            />
          </div>
          <div>
            <label className="text-sm text-noc-muted mb-1 block">IP / Host</label>
            <input
              type="text"
              className="input-field"
              value={form.ip}
              onChange={e => setForm({ ...form, ip: e.target.value })}
              placeholder="e.g. 8.8.8.8 or google.com"
              required
              pattern="^[a-zA-Z0-9.\-]+$"
              title="Alphanumeric, dots, and hyphens only"
            />
          </div>
          <div>
            <label className="text-sm text-noc-muted mb-1 block">
              Interval: {form.interval}s
            </label>
            <input
              type="range"
              min="30"
              max="3600"
              step="30"
              className="w-full accent-noc-accent"
              value={form.interval}
              onChange={e => setForm({ ...form, interval: parseInt(e.target.value) })}
            />
            <div className="flex justify-between text-xs text-noc-dim mt-0.5">
              <span>30s</span>
              <span>3600s</span>
            </div>
          </div>
          <div>
            <label className="text-sm text-noc-muted mb-1 block">Ping Count</label>
            <input
              type="number"
              className="input-field"
              min="1"
              max="100"
              value={form.ping_count}
              onChange={e => setForm({ ...form, ping_count: parseInt(e.target.value) || 1 })}
            />
          </div>
          {error && <p className="text-sm text-noc-red">{error}</p>}
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-ghost flex-1">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn-primary flex-1">
              {loading ? 'Saving...' : isEdit ? 'Save Changes' : 'Add Target'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
