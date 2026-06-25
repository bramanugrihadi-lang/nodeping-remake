import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import KPICards from '../components/KPICards';
import TargetDetail from '../components/TargetDetail';
import api from '../api';

export default function DashboardPage() {
  const { selectedTarget, setSelectedTarget } = useOutletContext();
  const [summary, setSummary] = useState({
    total: 0,
    online: 0,
    offline: 0,
    avg_latency: 0,
  });

  useEffect(() => {
    fetchSummary();
    const interval = setInterval(fetchSummary, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchSummary = async () => {
    try {
      const { data } = await api.get('/sync-status');
      if (data.summary) {
        setSummary(data.summary);
      }
    } catch (err) {
      console.error('Failed to fetch summary:', err);
    }
  };

  const handleTargetDeleted = () => {
    setSelectedTarget(null);
    fetchSummary();
  };

  return (
    <div className="space-y-6">
      {/* KPI Row */}
      <KPICards summary={summary} />

      {/* Target Detail */}
      <TargetDetail target={selectedTarget} onDeleted={handleTargetDeleted} />
    </div>
  );
}
