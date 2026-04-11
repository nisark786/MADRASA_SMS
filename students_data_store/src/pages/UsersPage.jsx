import { useState, useEffect } from 'react';
import api from '../api/client';
import UserFormModal from '../components/admin/UserFormModal';
import Sidebar from '../components/layout/Sidebar';
import { 
  Users, 
  Plus, 
  Pencil, 
  Trash2, 
  Search,
  MoreVertical,
  Mail,
  Shield,
  Clock
} from 'lucide-react';

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [showModal, setShowModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);

  const fetchUsers = () => {
    setLoading(true);
    api.get('/users/')
      .then(({ data }) => setUsers(data))
      .catch((err) => console.error("Failed to load users", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleAdd = () => {
    setSelectedUser(null);
    setShowModal(true);
  };

  const handleEdit = (user) => {
    setSelectedUser(user);
    setShowModal(true);
  };

  const handleDelete = async (id, email) => {
    if (!window.confirm(`Are you sure you want to delete user ${email}?`)) return;
    try {
      await api.delete(`/users/${id}`);
      fetchUsers();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete user");
    }
  };

  const handleSave = () => {
    setShowModal(false);
    fetchUsers();
  };

  return (
    <div className="flex min-h-screen bg-gray-50/50 font-sans antialiased">
      <Sidebar />
      <main className="flex-1 p-8 md:p-12 overflow-y-auto min-w-0">
        <div className="flex flex-col gap-8 max-w-7xl mx-auto">
          
          <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-gray-200">
            <div className="flex items-center gap-4">
              <div className="bg-indigo-600 p-3 rounded-2xl shadow-lg shadow-indigo-100/50">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 leading-tight tracking-tight">System Users</h1>
                <p className="text-sm text-gray-400 font-medium">Manage administrative access and user accounts</p>
              </div>
            </div>
            <button 
              className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-bold shadow-lg shadow-indigo-100 hover:bg-indigo-700 hover:shadow-indigo-200 transition-all active:scale-95 flex items-center gap-2"
              onClick={handleAdd}
            >
              <Plus className="w-4 h-4" strokeWidth={3} />
              Add System User
            </button>
          </div>

          <div className="bg-white border border-gray-200 rounded-3xl overflow-hidden shadow-[0_4px_24px_rgba(0,0,0,0.02)]">
            {loading ? (
              <div className="p-20 text-center">
                <div className="inline-flex flex-col items-center gap-4">
                  <div className="w-10 h-10 border-4 border-indigo-50 border-t-indigo-500 rounded-full animate-spin" />
                  <p className="text-gray-400 font-bold text-xs uppercase tracking-widest">Compiling user database...</p>
                </div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm text-gray-700 min-w-[800px]">
                  <thead>
                    <tr className="bg-gray-50/50 border-b border-gray-200 font-bold text-gray-400 text-[0.7rem] uppercase tracking-[0.15em]">
                      <th className="px-6 py-5">Internal ID</th>
                      <th className="px-6 py-5">Legal Name</th>
                      <th className="px-6 py-5 text-center">Privileges</th>
                      <th className="px-6 py-5">Access Status</th>
                      <th className="px-6 py-5">Last Observed</th>
                      <th className="px-6 py-5 text-right w-24">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {users.map(u => (
                      <tr key={u.id} className="hover:bg-gray-50/50 transition-colors group">
                        <td className="px-6 py-5">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center text-gray-400 group-hover:bg-white group-hover:text-indigo-600 transition-colors">
                              <Shield className="w-4 h-4" />
                            </div>
                            <span className="font-mono font-bold text-gray-900">{u.username}</span>
                          </div>
                        </td>
                        <td className="px-6 py-5">
                          <div className="font-bold text-gray-900 leading-none">{u.first_name} {u.last_name}</div>
                          <div className="mt-1 text-[0.7rem] text-gray-400 font-medium lowercase flex items-center gap-1">
                            <Mail className="w-3 h-3" />
                            {u.email}
                          </div>
                        </td>
                        <td className="px-6 py-5 text-center">
                          <div className="flex flex-wrap justify-center gap-1 max-w-[140px] mx-auto">
                            {u.is_active && (
                              <span className="bg-indigo-50/80 text-indigo-600 text-[0.6rem] font-black uppercase px-2 py-0.5 rounded-md border border-indigo-100">Auth</span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-5">
                          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[0.65rem] font-bold uppercase tracking-widest border ${u.is_active ? 'bg-emerald-50 text-emerald-700 border-emerald-100' : 'bg-gray-50 text-gray-500 border-gray-100'}`}>
                            <div className={`w-1.5 h-1.5 rounded-full ${u.is_active ? 'bg-emerald-500' : 'bg-gray-400'}`} />
                            {u.is_active ? 'Active' : 'Revoked'}
                          </span>
                        </td>
                        <td className="px-6 py-5 text-gray-400">
                          <div className="flex items-center gap-2 font-medium text-[0.75rem]">
                            <Clock className="w-3.5 h-3.5" />
                            {u.last_login ? new Date(u.last_login).toLocaleDateString() : 'Never Active'}
                          </div>
                        </td>
                        <td className="px-6 py-5 text-right relative">
                          <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto transition-all translate-x-1 group-hover:translate-x-0">
                            <button 
                              className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all" 
                              onClick={() => handleEdit(u)}
                            >
                              <Pencil className="w-4 h-4" />
                            </button>
                            <button 
                              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all" 
                              onClick={() => handleDelete(u.id, u.email)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                          <MoreVertical className="w-4 h-4 text-gray-300 ml-auto group-hover:hidden" />
                        </td>
                      </tr>
                    ))}
                    {users.length === 0 && (
                      <tr>
                        <td colSpan="6" className="text-center py-20">
                          <div className="flex flex-col items-center gap-4 text-gray-300">
                            <Shield className="w-12 h-12" strokeWidth={1} />
                            <p className="font-bold text-gray-900">No Administrators Found</p>
                            <p className="text-sm max-w-xs text-gray-500 leading-relaxed">The system user database is empty. You can add the first user using the button above.</p>
                          </div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {showModal && (
            <UserFormModal 
              user={selectedUser} 
              onClose={() => setShowModal(false)} 
              onSave={handleSave} 
            />
          )}
        </div>
      </main>
    </div>
  );
}
