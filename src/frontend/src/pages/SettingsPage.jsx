import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Settings as SettingsIcon,
  MessageCircle,
  Users,
  Save,
  Trash2,
  Plus,
  Eye,
  EyeOff,
  AlertTriangle,
  CheckCircle,
  Loader2,
} from 'lucide-react';
import api from '../api';

const TABS = [
  { id: 'telegram', label: 'Telegram', icon: MessageCircle },
  { id: 'users', label: 'Users', icon: Users },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('telegram');

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <SettingsIcon size={22} className="text-noc-accent" />
        <h1 className="text-xl font-bold">Settings</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-noc-surface border border-noc-border rounded-lg p-1 w-fit">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors
                ${
                  activeTab === tab.id
                    ? 'bg-noc-accent text-white'
                    : 'text-noc-muted hover:text-noc-text hover:bg-noc-card'
                }`}
            >
              <Icon size={15} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      {activeTab === 'telegram' && <TelegramConfig />}
      {activeTab === 'users' && <UserManagement />}
    </div>
  );
}

/* ─── Telegram Config ─── */
function TelegramConfig() {
  const [token, setToken] = useState('');
  const [chatId, setChatId] = useState('');
  const [showToken, setShowToken] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/settings/telegram');
      setToken(data.token || '');
      setChatId(data.chat_id || '');
    } catch (err) {
      console.error('Failed to load telegram settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      await api.post('/settings/telegram', { token, chat_id: chatId });
      setMessage({ type: 'success', text: 'Telegram settings saved' });
    } catch (err) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to save settings',
      });
    } finally {
      setSaving(false);
      setTimeout(() => setMessage(null), 4000);
    }
  };

  if (loading) {
    return (
      <div className="card flex items-center justify-center py-12 text-noc-dim">
        <Loader2 size={20} className="animate-spin mr-2" />
        Loading...
      </div>
    );
  }

  return (
    <div className="card max-w-lg">
      <h3 className="text-sm font-semibold text-noc-muted mb-4 flex items-center gap-2">
        <MessageCircle size={16} />
        Telegram Bot Configuration
      </h3>

      <form onSubmit={handleSave} className="space-y-4">
        <div>
          <label className="text-sm text-noc-muted mb-1.5 block">
            Bot Token
          </label>
          <div className="relative">
            <input
              type={showToken ? 'text' : 'password'}
              className="input-field pr-10 font-mono text-sm"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="123456:ABC-DEF..."
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showToken)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-noc-dim hover:text-noc-muted"
            >
              {showToken ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          <p className="text-xs text-noc-dim mt-1">
            {token && !showToken
              ? 'Token is masked. Toggle to reveal.'
              : 'Get from @BotFather on Telegram'}
          </p>
        </div>

        <div>
          <label className="text-sm text-noc-muted mb-1.5 block">
            Chat ID
          </label>
          <input
            type="text"
            className="input-field font-mono text-sm"
            value={chatId}
            onChange={(e) => setChatId(e.target.value)}
            placeholder="-1001234567890"
          />
          <p className="text-xs text-noc-dim mt-1">
            Group/channel/chat ID for alert delivery
          </p>
        </div>

        {message && (
          <div
            className={`flex items-center gap-2 text-sm rounded-lg p-3 border
            ${
              message.type === 'success'
                ? 'bg-noc-green/10 border-noc-green/20 text-noc-green'
                : 'bg-noc-red/10 border-noc-red/20 text-noc-red'
            }`}
          >
            {message.type === 'success' ? (
              <CheckCircle size={16} />
            ) : (
              <AlertTriangle size={16} />
            )}
            {message.text}
          </div>
        )}

        <button
          type="submit"
          disabled={saving}
          className="btn-primary flex items-center gap-2"
        >
          {saving ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Save size={16} />
          )}
          {saving ? 'Saving...' : 'Save Configuration'}
        </button>
      </form>
    </div>
  );
}

/* ─── User Management ─── */
function UserManagement() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    role: 'viewer',
  });
  const [addError, setAddError] = useState('');
  const [addLoading, setAddLoading] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const { data } = await api.get('/users');
      setUsers(data);
    } catch (err) {
      console.error('Failed to fetch users:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    setAddError('');
    setAddLoading(true);
    try {
      await api.post('/users', newUser);
      setShowAdd(false);
      setNewUser({ username: '', password: '', role: 'viewer' });
      fetchUsers();
    } catch (err) {
      setAddError(err.response?.data?.detail || 'Failed to create user');
    } finally {
      setAddLoading(false);
    }
  };

  const handleDeleteUser = async (userId, username) => {
    if (!confirm(`Delete user "${username}"?`)) return;
    try {
      await api.delete(`/users/${userId}`);
      fetchUsers();
    } catch (err) {
      console.error('Failed to delete user:', err);
    }
  };

  if (loading) {
    return (
      <div className="card flex items-center justify-center py-12 text-noc-dim">
        <Loader2 size={20} className="animate-spin mr-2" />
        Loading...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-noc-muted flex items-center gap-2">
          <Users size={16} />
          User Accounts
        </h3>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="btn-primary flex items-center gap-1.5 text-sm py-1.5 px-3"
        >
          <Plus size={14} />
          Add User
        </button>
      </div>

      {/* Add form */}
      {showAdd && (
        <div className="card">
          <h4 className="text-sm font-medium mb-3">New User</h4>
          <form onSubmit={handleAddUser} className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-xs text-noc-muted mb-1 block">
                  Username
                </label>
                <input
                  type="text"
                  className="input-field text-sm"
                  value={newUser.username}
                  onChange={(e) =>
                    setNewUser({ ...newUser, username: e.target.value })
                  }
                  placeholder="username"
                  required
                />
              </div>
              <div>
                <label className="text-xs text-noc-muted mb-1 block">
                  Password
                </label>
                <input
                  type="password"
                  className="input-field text-sm"
                  value={newUser.password}
                  onChange={(e) =>
                    setNewUser({ ...newUser, password: e.target.value })
                  }
                  placeholder="password"
                  required
                  minLength={4}
                />
              </div>
              <div>
                <label className="text-xs text-noc-muted mb-1 block">
                  Role
                </label>
                <select
                  className="input-field text-sm"
                  value={newUser.role}
                  onChange={(e) =>
                    setNewUser({ ...newUser, role: e.target.value })
                  }
                >
                  <option value="viewer">Viewer</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            </div>
            {addError && (
              <p className="text-sm text-noc-red flex items-center gap-1">
                <AlertTriangle size={14} />
                {addError}
              </p>
            )}
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setShowAdd(false)}
                className="btn-ghost text-sm py-1.5 px-3"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={addLoading}
                className="btn-primary text-sm py-1.5 px-3"
              >
                {addLoading ? 'Creating...' : 'Create User'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Users table */}
      <div className="card overflow-hidden p-0">
        <table className="w-full">
          <thead>
            <tr className="border-b border-noc-border">
              <th className="text-left text-xs font-medium text-noc-muted px-4 py-3">
                Username
              </th>
              <th className="text-left text-xs font-medium text-noc-muted px-4 py-3">
                Role
              </th>
              <th className="text-right text-xs font-medium text-noc-muted px-4 py-3">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 ? (
              <tr>
                <td
                  colSpan={3}
                  className="text-center py-8 text-noc-dim text-sm"
                >
                  No users found
                </td>
              </tr>
            ) : (
              users.map((u) => (
                <tr
                  key={u.id}
                  className="border-b border-noc-border/50 last:border-0"
                >
                  <td className="px-4 py-3 text-sm font-medium">
                    <div className="flex items-center gap-2">
                      {u.username}
                      {u.id === currentUser?.id && (
                        <span className="text-xs bg-noc-accent/20 text-noc-accent px-1.5 py-0.5 rounded">
                          you
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium
                      ${
                        u.role === 'admin'
                          ? 'bg-noc-accent/10 text-noc-accent'
                          : 'bg-noc-card text-noc-muted'
                      }`}
                    >
                      {u.role}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {u.id !== currentUser?.id ? (
                      <button
                        onClick={() => handleDeleteUser(u.id, u.username)}
                        className="btn-ghost p-1.5 text-noc-red hover:bg-noc-red/10"
                        title="Delete user"
                      >
                        <Trash2 size={14} />
                      </button>
                    ) : (
                      <span className="text-xs text-noc-dim">—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
