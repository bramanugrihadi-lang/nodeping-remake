import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Pencil, Trash2, Wifi, WifiOff, Clock, ArrowUp } from 'lucide-react';
import LatencyChart from './LatencyChart';
import TargetForm from './TargetForm';
import api from '../api';

export default function TargetDetail({ target, onDeleted }) {
  const { isAdmin } = useAuth();
  const [history, setHistory] = useState([]);
  const [editMode, setEditMode] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (target) fetchHistory();
  }, [target?.name]);

  const fetchHistory = async () => {
    if (!target) return;
    try {
      const since = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
      const { data } = await api.get(`/history/${target.name}`, { params: { since } });
      setHistory(data);
    } catch {}
  };

  const handleDelete = async () => {
    if (!confirm(`Delete target "${target.name}"?`)) return;
    setDeleting(true);
    try {
      await api.delete(`/targets/${target.id}`);
      onDeleted?.();
    } catch {} finally {
      setDeleting(false);
    }
  };

  if (!target) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-noc-dim">
        <Wifi size={48} className="mb-3 opacity-30" />
        <p className="text-lg">Select a target to view details</p>
        <p className="text-sm mt-1">Or add a new monitoring target from the sidebar</p>
      </div>
    );
  }

  // Calculate uptime from history
  const totalPings = history.length;
  const onlinePings = history.filter(h => h.loss <= 50).length;
  const uptimePercent = totalPings > 0 ? ((onlinePings / totalPings) * 100).toFixed(1) : '—';
  const avgLatency = totalPings > 0
    ? (history.reduce((s, h) => s + h.avg_latency, 0) / totalPings).toFixed(1)
    : '—';

  return (
    <div className="space-y-6">
      {/* Target header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            {target.is_online ? (
              <Wifi size={20} className="text-noc-green" />
            ) : (
              <WifiOff size={20} className="text-noc-red" />
            )}
            <h2 className="text-xl font-bold">{target.name}</h2>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium
              ${target.is_online
                ? 'bg-noc-green/10 text-noc-green'
                : 'bg-noc-red/10 text-noc-red'
              }`}>
              {target.is_online ? 'ONLINE' : 'OFFLINE'}
            </span>
          </div>
          <p className="text-noc-muted text-sm mt-1 font-mono">{target.ip}</p>
        </div>
        {isAdmin && (
          <div className="flex gap-2">
            <button
              onClick={() => setEditMode(true)}
              className="btn-ghost p-2"
              title="Edit"
            >
              <Pencil size={16} />
            </button>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="btn-ghost p-2 text-noc-red hover:bg-noc-red/10"
              title="Delete"
            >
              <Trash2 size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard
          icon={Wifi}
          label="Status"
          value={target.is_online ? 'Online' : 'Offline'}
          color={target.is_online ? 'text-noc-green' : 'text-noc-red'}
        />
        <StatCard
          icon={ArrowUp}
          label="Uptime (24h)"
          value={`${uptimePercent}%`}
          color="text-noc-accent"
        />
        <StatCard
          icon={Clock}
          label="Avg Latency"
          value={`${avgLatency} ms`}
          color="text-noc-yellow"
        />
        <StatCard
          icon={WifiOff}
          label="Last Loss"
          value={`${target.last_loss.toFixed(1)}%`}
          color={target.last_loss > 0 ? 'text-noc-red' : 'text-noc-green'}
        />
      </div>

      {/* Chart */}
      <div className="card">
        <h3 className="text-sm font-semibold text-noc-muted mb-3">
          Latency & Packet Loss (24h)
        </h3>
        <LatencyChart targetName={target.name} />
      </div>

      {/* Config info */}
      <div className="card">
        <h3 className="text-sm font-semibold text-noc-muted mb-3">Configuration</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-noc-dim">Interval</span>
            <p className="font-mono">{target.interval}s</p>
          </div>
          <div>
            <span className="text-noc-dim">Ping Count</span>
            <p className="font-mono">{target.ping_count} packets</p>
          </div>
          <div>
            <span className="text-noc-dim">Data Points</span>
            <p className="font-mono">{totalPings}</p>
          </div>
        </div>
      </div>

      {/* Edit modal */}
      {editMode && (
        <TargetForm
          target={target}
          onClose={() => setEditMode(false)}
          onSaved={() => { setEditMode(false); }}
        />
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="card flex items-center gap-3">
      <div className={`w-8 h-8 rounded-lg bg-noc-card flex items-center justify-center`}>
        <Icon size={16} className={color} />
      </div>
      <div>
        <div className={`text-lg font-bold font-mono ${color}`}>{value}</div>
        <div className="text-xs text-noc-dim">{label}</div>
      </div>
    </div>
  );
}
