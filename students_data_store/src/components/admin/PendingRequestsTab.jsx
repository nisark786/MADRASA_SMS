import { useState, useEffect } from 'react';
import api from '../../api/client';
import { 
  CheckCircle, 
  XCircle, 
  Eye, 
  Inbox,
  AlertTriangle,
  Clock
} from 'lucide-react';

export default function PendingRequestsTab() {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modals
  const [viewData, setViewData] = useState(null);
  const [conflictData, setConflictData] = useState(null); // When approval fails with 409

  const loadSubmissions = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/forms/submissions/all');
      setSubmissions(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSubmissions();
  }, []);

  const handleApprove = async (sub_id, force_update = false) => {
    try {
      await api.post(`/forms/submissions/${sub_id}/approve`, { force_update });
      setConflictData(null);
      alert('Approved successfully!');
      loadSubmissions();
    } catch (err) {
      if (err.response?.status === 409) {
        setConflictData({ sub_id, detail: err.response.data.detail });
      } else {
        alert(err.response?.data?.detail || 'Failed to approve');
      }
    }
  };

  const handleReject = async (sub_id) => {
    if (!window.confirm('Reject this submission? This cannot be undone.')) return;
    try {
      await api.post(`/forms/submissions/${sub_id}/reject`);
      loadSubmissions();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to reject');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Pending Requests</h2>
          <p className="text-sm text-gray-500">Review public form submissions before adding them to the main directory.</p>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-700 min-w-[800px]">
             <thead>
              <tr className="bg-gray-50 border-b border-gray-100 uppercase text-[0.7rem] font-bold text-gray-400 tracking-wider">
                <th className="px-6 py-4">Submitted Date</th>
                <th className="px-6 py-4">Student Info</th>
                <th className="px-6 py-4">Form Source</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr><td colSpan="5" className="px-6 py-12 text-center text-gray-400">Loading submissions...</td></tr>
              ) : submissions.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-16 text-center text-gray-400">
                    <div className="flex flex-col items-center">
                      <Inbox className="w-10 h-10 mb-2 text-gray-300" />
                      <p>No submissions found.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                submissions.map(sub => (
                  <tr key={sub.id} className="hover:bg-gray-50/50">
                    <td className="px-6 py-4 whitespace-nowrap text-gray-500 text-xs">
                      <div className="flex items-center gap-1.5 font-medium">
                        <Clock className="w-3.5 h-3.5" />
                        {new Date(sub.submitted_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-bold text-gray-900">{sub.data.first_name} {sub.data.last_name}</div>
                      <div className="text-xs text-gray-500">{sub.data.email}</div>
                    </td>
                    <td className="px-6 py-4">
                       <span className="text-xs font-bold bg-gray-100 text-gray-600 px-2.5 py-1 rounded-lg">
                          {sub.form_title}
                       </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold capitalize ${
                        sub.status === 'pending' ? 'bg-amber-100 text-amber-800' :
                        sub.status === 'approved' ? 'bg-green-100 text-green-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {sub.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button 
                          onClick={() => setViewData(sub)} 
                          className="p-1.5 text-gray-400 hover:text-indigo-600 rounded-lg hover:bg-gray-100" 
                          title="View Data"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        {sub.status === 'pending' && (
                          <>
                            <button 
                              onClick={() => handleApprove(sub.id, false)} 
                              className="p-1.5 text-gray-400 hover:text-green-600 rounded-lg hover:bg-green-50" 
                              title="Approve"
                            >
                              <CheckCircle className="w-4 h-4" />
                            </button>
                            <button 
                              onClick={() => handleReject(sub.id)} 
                              className="p-1.5 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50" 
                              title="Reject"
                            >
                              <XCircle className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* View Data Modal */}
      {viewData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 backdrop-blur-sm">
          <div className="bg-white w-full max-w-lg rounded-3xl p-8 shadow-2xl relative">
            <button onClick={() => setViewData(null)} className="absolute top-6 right-6 text-gray-400 hover:text-gray-900">
              <XCircle className="w-6 h-6" />
            </button>
            <h2 className="text-xl font-bold mb-6">Submission Details</h2>
            <div className="bg-gray-50 rounded-xl p-4 max-h-[60vh] overflow-y-auto font-mono text-xs">
              <pre>{JSON.stringify(viewData.data, null, 2)}</pre>
            </div>
          </div>
        </div>
      )}

      {/* Conflict Resolution Modal */}
      {conflictData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 backdrop-blur-sm">
           <div className="bg-white w-full max-w-md rounded-3xl p-8 shadow-2xl relative border-t-8 border-amber-500">
             <div className="flex flex-col items-center text-center">
                <div className="bg-amber-100 p-4 rounded-full text-amber-600 mb-4">
                  <AlertTriangle className="w-10 h-10" />
                </div>
                <h2 className="text-xl font-bold text-gray-900 mb-2">Record Conflict</h2>
                <p className="text-sm text-gray-500 mb-6 px-4">
                  {conflictData.detail.message} <br/>
                  Conflicting Student: <strong>{conflictData.detail.conflicting_student_name}</strong>
                </p>
                <div className="w-full flex gap-3">
                  <button onClick={() => setConflictData(null)} className="flex-1 py-2.5 rounded-xl text-gray-500 text-sm font-bold bg-gray-100 hover:bg-gray-200">
                    Cancel
                  </button>
                  <button onClick={() => handleApprove(conflictData.sub_id, true)} className="flex-1 py-2.5 rounded-xl text-white text-sm font-bold bg-amber-500 hover:bg-amber-600 shadow-lg shadow-amber-200">
                    Update Existing
                  </button>
                </div>
             </div>
           </div>
        </div>
      )}
    </div>
  );
}
