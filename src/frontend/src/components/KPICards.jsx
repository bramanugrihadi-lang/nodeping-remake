import { Monitor, Wifi, WifiOff, Clock } from 'lucide-react';

export default function KPICards({ summary }) {
  const cards = [
    {
      label: 'Total Targets',
      value: summary.total,
      icon: Monitor,
      color: 'text-noc-accent',
      bg: 'bg-noc-accent/10',
    },
    {
      label: 'Online',
      value: summary.online,
      icon: Wifi,
      color: 'text-noc-green',
      bg: 'bg-noc-green/10',
    },
    {
      label: 'Offline',
      value: summary.offline,
      icon: WifiOff,
      color: 'text-noc-red',
      bg: 'bg-noc-red/10',
    },
    {
      label: 'Avg Loss',
      value: `${summary.avg_latency?.toFixed(1) || '0.0'}%`,
      icon: Clock,
      color: 'text-noc-yellow',
      bg: 'bg-noc-yellow/10',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map(({ label, value, icon: Icon, color, bg }) => (
        <div key={label} className="card flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center`}>
            <Icon size={20} className={color} />
          </div>
          <div>
            <div className="text-2xl font-bold font-mono">{value}</div>
            <div className="text-xs text-noc-muted">{label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
