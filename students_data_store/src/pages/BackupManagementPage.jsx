import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../store/authStore';
import { Download, Trash2, RotateCcw, Plus, AlertCircle, CheckCircle, Clock, XCircle, Cloud, CloudUpload } from 'lucide-react';
import api from '../services/api';

const BackupManagementPage = () => {
  const { user } = useAuthStore();
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [creating, setCreating] = useState(false);
  const [statusFilter, setStatusFilter] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);
  const [showRestoreConfirm, setShowRestoreConfirm] = useState(null);
  const [uploadToGoogleDrive, setUploadToGoogleDrive] = useState(false);
  const [googleDriveStorageInfo, setGoogleDriveStorageInfo] = useState(null);
  const [uploadingToGoogleDrive, setUploadingToGoogleDrive] = useState(null);

  useEffect(() => {
    fetchBackups();
    fetchSummary();
    fetchGoogleDriveStorageInfo();
  }, [page, statusFilter]);

  const fetchBackups = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.append('page', page);
      params.append('page_size', 20);
      if (statusFilter) {
        params.append('status', statusFilter);
      }

      const response = await api.get(`/backups?${params}`);
      setBackups(response.data.backups);
      setTotalPages(response.data.pages);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch backups');
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await api.get('/backups/stats/summary');
      setSummary(response.data);
    } catch (err) {
      console.error('Failed to fetch backup summary:', err);
    }
  };

  const fetchGoogleDriveStorageInfo = async () => {
    try {
      const response = await api.get('/backups/google-drive/storage-info');
      setGoogleDriveStorageInfo(response.data);
    } catch (err) {
      console.error('Failed to fetch Google Drive storage info:', err);
    }
  };

  const handleCreateBackup = async () => {
    try {
      setCreating(true);
      const params = new URLSearchParams();
      params.append('description', `Manual backup created at ${new Date().toLocaleString()}`);
      params.append('upload_to_drive', uploadToGoogleDrive);
      
      const response = await api.post(`/backups?${params}`);
      if (response.data.success) {
        setPage(1);
        fetchBackups();
        fetchSummary();
        setUploadToGoogleDrive(false);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create backup');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteBackup = async (backupId) => {
    try {
      const response = await api.delete(`/backups/${backupId}`);
      if (response.data.success) {
        fetchBackups();
        fetchSummary();
        setShowDeleteConfirm(null);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete backup');
    }
  };

  const handleRestoreBackup = async (backupId) => {
    try {
      const response = await api.post(`/backups/${backupId}/restore`);
      if (response.data.success) {
        fetchBackups();
        setShowRestoreConfirm(null);
        alert('Database restore initiated. This may take several minutes.');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to restore backup');
    }
  };

  const handleUploadToGoogleDrive = async (backupId) => {
    try {
      setUploadingToGoogleDrive(backupId);
      const response = await api.post(`/backups/${backupId}/upload-to-drive`);
      if (response.data.success) {
        fetchBackups();
        alert('Backup uploaded to Google Drive successfully!');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload backup to Google Drive');
    } finally {
      setUploadingToGoogleDrive(null);
    }
  };

  const handleDeleteFromGoogleDrive = async (backupId) => {
    try {
      setUploadingToGoogleDrive(backupId);
      const response = await api.delete(`/backups/${backupId}/delete-from-drive`);
      if (response.data.success) {
        fetchBackups();
        alert('Backup deleted from Google Drive');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete backup from Google Drive');
    } finally {
      setUploadingToGoogleDrive(null);
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: Clock, label: 'Pending' },
      in_progress: { bg: 'bg-blue-100', text: 'text-blue-800', icon: Clock, label: 'In Progress' },
      completed: { bg: 'bg-green-100', text: 'text-green-800', icon: CheckCircle, label: 'Completed' },
      failed: { bg: 'bg-red-100', text: 'text-red-800', icon: XCircle, label: 'Failed' },
    };
    const statusInfo = statusMap[status] || { bg: 'bg-gray-100', text: 'text-gray-800', icon: AlertCircle, label: 'Unknown' };
    const Icon = statusInfo.icon;
    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${statusInfo.bg} ${statusInfo.text}`}>
        <Icon size={16} />
        {statusInfo.label}
      </span>
    );
  };

  const formatBytes = (bytes) => {
    if (!bytes) return 'N/A';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(2)} ${units[unitIndex]}`;
  };

  const formatDateTime = (datetime) => {
    if (!datetime) return 'N/A';
    return new Date(datetime).toLocaleString();
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Database Backups</h1>
          <p className="text-gray-600">Manage and monitor your database backups</p>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-gray-600 text-sm font-medium mb-2">Total Backups</div>
              <div className="text-2xl font-bold text-gray-900">{summary.total_backups}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-gray-600 text-sm font-medium mb-2">Completed</div>
              <div className="text-2xl font-bold text-green-600">{summary.completed_backups}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-gray-600 text-sm font-medium mb-2">Failed</div>
              <div className="text-2xl font-bold text-red-600">{summary.failed_backups}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-gray-600 text-sm font-medium mb-2">Total Size</div>
              <div className="text-2xl font-bold text-gray-900">{formatBytes(summary.total_size)}</div>
            </div>
          </div>
        )}

        {/* Google Drive Storage Info */}
        {googleDriveStorageInfo && googleDriveStorageInfo.enabled && (
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-start gap-4">
              <Cloud className="text-blue-600 flex-shrink-0 mt-1" size={24} />
              <div className="flex-1">
                <h3 className="font-semibold text-blue-900 mb-2">Google Drive Storage</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-blue-700 font-medium">Used</p>
                    <p className="text-blue-600">{googleDriveStorageInfo.usage_gb?.toFixed(2)} GB / {googleDriveStorageInfo.limit_gb?.toFixed(2)} GB</p>
                  </div>
                  <div>
                    <p className="text-blue-700 font-medium">Available</p>
                    <p className="text-blue-600">{googleDriveStorageInfo.available_gb?.toFixed(2)} GB</p>
                  </div>
                  <div>
                    <p className="text-blue-700 font-medium">Status</p>
                    <p className="text-green-600">✓ Connected</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-gap-3">
            <AlertCircle className="text-red-600 flex-shrink-0" />
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="mb-6 flex flex-col gap-3">
          <div className="flex gap-3 flex-wrap items-center">
            <button
              onClick={handleCreateBackup}
              disabled={creating}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              <Plus size={20} />
              {creating ? 'Creating...' : 'Create Backup'}
            </button>
            <select
              value={statusFilter || ''}
              onChange={(e) => {
                setStatusFilter(e.target.value || null);
                setPage(1);
              }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="in_progress">In Progress</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          {googleDriveStorageInfo && googleDriveStorageInfo.enabled && (
            <label className="flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg cursor-pointer hover:bg-blue-100 transition-colors">
              <input
                type="checkbox"
                checked={uploadToGoogleDrive}
                onChange={(e) => setUploadToGoogleDrive(e.target.checked)}
                className="w-4 h-4 text-blue-600"
              />
              <CloudUpload size={16} className="text-blue-600" />
              <span className="text-sm font-medium text-blue-900">Upload to Google Drive</span>
            </label>
          )}
        </div>

        {/* Backups Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-gray-600">Loading backups...</div>
          ) : backups.length === 0 ? (
            <div className="p-8 text-center text-gray-600">No backups found</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Size</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Duration</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Created</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Drive</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {backups.map((backup) => (
                    <tr key={backup.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">{backup.name}</td>
                      <td className="px-6 py-4 text-sm">{getStatusBadge(backup.status)}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{formatBytes(backup.file_size)}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          {backup.backup_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {backup.duration_seconds ? `${backup.duration_seconds}s` : 'N/A'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">{formatDateTime(backup.created_at)}</td>
                      <td className="px-6 py-4 text-sm">
                        {backup.uploaded_to_drive ? (
                          <div className="flex items-center gap-2">
                            <Cloud size={16} className="text-blue-600" />
                            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Synced</span>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-500">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <div className="flex gap-1 flex-wrap">
                          {backup.status === 'completed' && (
                            <>
                              <button
                                onClick={() => setShowRestoreConfirm(backup.id)}
                                title="Restore from this backup"
                                className="p-2 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                              >
                                <RotateCcw size={16} />
                              </button>
                              {!backup.uploaded_to_drive && (
                                <button
                                  onClick={() => handleUploadToGoogleDrive(backup.id)}
                                  disabled={uploadingToGoogleDrive === backup.id}
                                  title="Upload to Google Drive"
                                  className="p-2 text-purple-600 hover:bg-purple-50 rounded transition-colors disabled:opacity-50"
                                >
                                  <CloudUpload size={16} />
                                </button>
                              )}
                              {backup.uploaded_to_drive && (
                                <button
                                  onClick={() => handleDeleteFromGoogleDrive(backup.id)}
                                  disabled={uploadingToGoogleDrive === backup.id}
                                  title="Remove from Google Drive"
                                  className="p-2 text-purple-600 hover:bg-purple-50 rounded transition-colors disabled:opacity-50"
                                >
                                  <Cloud size={16} />
                                </button>
                              )}
                            </>
                          )}
                          <button
                            onClick={() => setShowDeleteConfirm(backup.id)}
                            title="Delete backup"
                            className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-6 flex items-center justify-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="px-3 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>
            <span className="text-sm text-gray-600">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="px-3 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-lg max-w-sm w-full p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Delete Backup?</h3>
              <p className="text-gray-600 mb-6">
                Are you sure you want to delete this backup? This action cannot be undone.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowDeleteConfirm(null)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDeleteBackup(showDeleteConfirm)}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Restore Confirmation Modal */}
        {showRestoreConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-lg max-w-sm w-full p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Restore Database?</h3>
              <p className="text-gray-600 mb-2">
                Are you sure you want to restore from this backup?
              </p>
              <p className="text-red-600 text-sm font-semibold mb-6">
                ⚠️ This will overwrite your current database. Make sure you have a backup first!
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowRestoreConfirm(null)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleRestoreBackup(showRestoreConfirm)}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Restore
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BackupManagementPage;
