import { useEffect, useState } from 'react';
import { Mail, Search, RefreshCw, AlertCircle } from 'lucide-react';
import { API_BASE_URL } from '../api/config';
import Sidebar from '../components/layout/Sidebar';

export default function EmailHistoryPage() {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [refreshing, setRefreshing] = useState(false);

  const fetchEmails = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`${API_BASE_URL}/emails/history`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch email history');
      }

      const data = await response.json();
      setEmails(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching emails:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmails();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchEmails();
    setRefreshing(false);
  };

  const filteredEmails = emails.filter(email => {
    const matchesSearch = 
      email.recipient_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      email.subject.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || email.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'sent':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'bounced':
        return 'bg-pink-100 text-pink-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'sent':
        return '✓';
      case 'pending':
        return '⏳';
      case 'failed':
        return '✕';
      case 'bounced':
        return '↩️';
      default:
        return '?';
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-50/50 font-sans">
      <Sidebar />
      <main className="flex-1 p-8 md:p-12 overflow-y-auto min-w-0">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-start justify-between mb-8">
            <div>
              <div className="flex items-center gap-2.5 mb-2">
                <div className="bg-indigo-600 p-2 rounded-xl">
                  <Mail className="w-5 h-5 text-white" />
                </div>
                <h1 className="text-2xl font-bold text-gray-900 leading-tight tracking-tight">Email History</h1>
              </div>
              <p className="text-sm text-gray-500 font-medium ml-1">
                View all sent and pending emails
              </p>
            </div>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-gray-700 font-semibold hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>

          {/* Filters */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6 shadow-sm">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Search</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Email or subject..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Status</label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="all">All Statuses</option>
                  <option value="sent">Sent</option>
                  <option value="pending">Pending</option>
                  <option value="failed">Failed</option>
                  <option value="bounced">Bounced</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Total</label>
                <div className="px-4 py-2 bg-indigo-50 border border-indigo-200 rounded-lg">
                  <p className="text-lg font-bold text-indigo-600">{filteredEmails.length}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-semibold text-red-900">Error</p>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          )}

          {/* Loading State */}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-indigo-100 mb-4">
                  <RefreshCw className="w-6 h-6 text-indigo-600 animate-spin" />
                </div>
                <p className="text-gray-600 font-medium">Loading email history...</p>
              </div>
            </div>
          ) : filteredEmails.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
              <Mail className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600 font-medium">No emails found</p>
              <p className="text-sm text-gray-500">
                {searchTerm || statusFilter !== 'all' ? 'Try adjusting your filters' : 'Email history will appear here'}
              </p>
            </div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Recipient</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Subject</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Sent At</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Created</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {filteredEmails.map((email) => (
                      <tr key={email.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex flex-col">
                            <p className="font-medium text-gray-900">{email.recipient_name || 'N/A'}</p>
                            <p className="text-sm text-gray-500">{email.recipient_email}</p>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <p className="text-sm text-gray-900 truncate" title={email.subject}>{email.subject}</p>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadgeClass(email.status)}`}>
                            <span>{getStatusIcon(email.status)}</span>
                            {email.status.charAt(0).toUpperCase() + email.status.slice(1)}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <p className="text-sm text-gray-600">
                            {email.sent_at ? new Date(email.sent_at).toLocaleString() : '-'}
                          </p>
                        </td>
                        <td className="px-6 py-4">
                          <p className="text-sm text-gray-600">
                            {new Date(email.created_at).toLocaleString()}
                          </p>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
