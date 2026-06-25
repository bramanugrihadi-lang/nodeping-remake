import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, AreaChart
} from 'recharts';
import api from '../api';

export default function LatencyChart({ targetName, height = 300 }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!targetName) return;
    fetchHistory();
    const interval = setInterval(fetchHistory, 10000);
    return () => clearInterval(interval);
  }, [targetName]);

  const fetchHistory = async () => {
    try {
      const since = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
      const { data: history } = await api.get(`/history/${targetName}`, {
        params: { since }
      });
      const formatted = history.map(h => ({
        ...h,
        time: new Date(h.timestamp).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
        }),
        date: new Date(h.timestamp).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        }),
      }));
      setData(formatted);
    } catch {} finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[300px] text-noc-dim">
        Loading chart...
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-noc-dim">
        No history data yet
      </div>
    );
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="bg-noc-card border border-noc-border rounded-lg p-3 shadow-xl">
        <p className="text-xs text-noc-muted mb-1">{label}</p>
        {payload.map((p, i) => (
          <p key={i} className="text-sm" style={{ color: p.color }}>
            {p.name}: <span className="font-mono font-bold">{p.value?.toFixed(1)}</span>
            {p.dataKey === 'avg_latency' ? ' ms' : '%'}
          </p>
        ))}
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
        <defs>
          <linearGradient id="latencyGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="lossGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis
          dataKey="time"
          tick={{ fontSize: 11, fill: '#64748b' }}
          tickLine={false}
          axisLine={{ stroke: '#1e293b' }}
          interval="preserveStartEnd"
        />
        <YAxis
          yAxisId="latency"
          tick={{ fontSize: 11, fill: '#64748b' }}
          tickLine={false}
          axisLine={false}
          unit=" ms"
        />
        <YAxis
          yAxisId="loss"
          orientation="right"
          tick={{ fontSize: 11, fill: '#64748b' }}
          tickLine={false}
          axisLine={false}
          unit="%"
          domain={[0, 100]}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          yAxisId="latency"
          type="monotone"
          dataKey="avg_latency"
          stroke="#3b82f6"
          strokeWidth={2}
          fill="url(#latencyGrad)"
          name="Latency"
          dot={false}
          activeDot={{ r: 4, fill: '#3b82f6' }}
        />
        <Area
          yAxisId="loss"
          type="stepAfter"
          dataKey="loss"
          stroke="#ef4444"
          strokeWidth={1.5}
          fill="url(#lossGrad)"
          name="Packet Loss"
          dot={false}
          activeDot={{ r: 4, fill: '#ef4444' }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
