import { useState, useEffect } from 'react';
import { Search, Plus, Wifi, WifiOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../api';

export default function Sidebar({ open, selectedTarget, onSelectTarget }) {
  const { isAdmin } = useAuth();
  const [targets, setTargets] = useState([]);
  const [search, setSearch] = useState('');
  const [summary, setSummary] = useState({ total: 0, online: 0, offline: 0 });
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const { data } = await api.get('/sync-status');
      setTargets(data.targets || []);
      setSummary(data.summary || { total: 0, online: 0, offline: 0 });
    } catch {}
  };

  const filtered = targets.filter(t =>
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    t.ip.toLowerCase().includes(search.toLowerCase())
  );

  if (!open) return null;

  return (
    <aside className="w-72 bg-noc-surface border-r border-noc-border flex flex-col shrink-0 overflow-hidden">
      {/* Summary counts */}
      <div className="p-3 border-b border-noc-border">
        <div className="flex items-center justify-between text-xs">
          <span className="text-noc-muted">Targets</span>
          <span className="font-mono font-bold">{summary.total}</span>
        </div>
        <div className="flex gap-3 mt-1.5">
          <div className="flex items-center gap-1 text-xs">
            <span className="w-2 h-2 rounded-full bg-noc-green" />
            <span className="text-noc-green font-mono">{summary.online}</span>
          </div>
          <div className="flex items-center gap-1 text-xs">
            <span className="w-2 h-2 rounded-full bg-noc-red" />
            <span className="text-noc-red font-mono">{summary.offline}</span>
          </div>
        </div>
      </div>

      {/* Search + Add */}
      <div className="p-3 border-b border-noc-border flex gap-2">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-noc-dim" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search targets..."
            className="input-field pl-8 text-sm py-1.5"
          />
        </div>
        {isAdmin && (
          <button
            onClick={() => setShowAddForm(true)}
            className="btn-primary p-1.5 rounded-lg"
            title="Add target"
          >
            <Plus size={16} />
          </button>
        )}
      </div>

      {/* Target list */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="p-4 text-center text-noc-dim text-sm">
            {targets.length === 0 ? 'No targets configured' : 'No matches'}
          </div>
        ) : (
          filtered.map(target => (
            <button
              key={target.id}
              onClick={() => onSelectTarget(target)}
              className={`w-full text-left px-3 py-2.5 border-b border-noc-border/50 flex items-center gap-3 transition-colors
                ${selectedTarget?.id === target.id
                  ? 'bg-noc-accent/10 border-l-2 border-l-noc-accent'
                  : 'hover:bg-noc-card border-l-2 border-l-transparent'
                }`}
            >
              {target.is_online ? (
                <Wifi size={14} className="text-noc-green shrink-0" />
              ) : (
                <WifiOff size={14} className="text-noc-red shrink-0" />
              )}
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium truncate">{target.name}</div>
                <div className="text-xs text-noc-dim truncate">{target.ip}</div>
              </div>
              <div className="text-right shrink-0">
                {target.is_online ? (
                  <span className="text-xs font-mono text-noc-green">
                    {target.last_loss.toFixed(0)}% loss
                  </span>
                ) : (
                  <span className="text-xs font-mono text-noc-red">DOWN</span>
                )}
              </div>
            </button>
          ))
        )}
      </div>

      {/* Add form modal - rendered at page level */}
      {showAddForm && (
        <AddTargetModal
          onClose={() => setShowAddForm(false)}
          onAdded={() => { setShowAddForm(false); fetchStatus(); }}
        />
      )}
    </aside>
  );
}

function AddTargetModal({ onClose, onAdded }) {
  const [form, setForm] = useState({ name: '', ip: '', interval: 60, ping_count: 4 });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.post('/targets', form);
      onAdded();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add target');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div className="card w-full max-w-md mx-4" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-semibold mb-4">Add Target</h3>
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
          <div className="grid grid-cols-2 gap-3">
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
          </div>
          {error && <p className="text-sm text-noc-red">{error}</p>}
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-ghost flex-1">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1">
              {loading ? 'Adding...' : 'Add Target'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
