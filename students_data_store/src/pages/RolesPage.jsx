import { useState, useEffect } from 'react';
import api from '../api/client';
import RoleFormModal from '../components/admin/RoleFormModal';
import Sidebar from '../components/layout/Sidebar';
import { 
  ShieldCheck, 
  Plus, 
  Pencil, 
  Trash2, 
  ShieldAlert,
  MoreVertical,
  Activity,
  Cpu
} from 'lucide-react';

export default function RolesPage() {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);

  const [showModal, setShowModal] = useState(false);
  const [selectedRole, setSelectedRole] = useState(null);

  const fetchRoles = () => {
    setLoading(true);
    api.get('/roles/')
      .then(({ data }) => setRoles(data))
      .catch((err) => console.error("Failed to load roles", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  const handleAdd = () => {
    setSelectedRole(null);
    setShowModal(true);
  };

  const handleEdit = (role) => {
    setSelectedRole(role);
    setShowModal(true);
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete role ${name}?`)) return;
    try {
      await api.delete(`/roles/${id}`);
      fetchRoles();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete role");
    }
  };

  const handleSave = () => {
    setShowModal(false);
    fetchRoles();
  };

  return (
    <div className="flex min-h-screen bg-gray-50/50 font-sans antialiased">
      <Sidebar />
      <main className="flex-1 p-8 md:p-12 overflow-y-auto min-w-0">
        <div className="flex flex-col gap-8 max-w-7xl mx-auto">
          
          <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-gray-200">
            <div className="flex items-center gap-4">
              <div className="bg-indigo-600 p-3 rounded-2xl shadow-lg shadow-indigo-100/50">
                <ShieldCheck className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 leading-tight tracking-tight">Access Control Roles</h1>
                <p className="text-sm text-gray-400 font-medium">Define security groups and configure resource permissions</p>
              </div>
            </div>
            <button 
              className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-bold shadow-lg shadow-indigo-100 hover:bg-indigo-700 hover:shadow-indigo-200 transition-all active:scale-95 flex items-center gap-2"
              onClick={handleAdd}
            >
              <Plus className="w-4 h-4" strokeWidth={3} />
              Create New Role
            </button>
          </div>

          <div className="bg-white border border-gray-200 rounded-3xl overflow-hidden shadow-[0_4px_24px_rgba(0,0,0,0.02)]">
            {loading ? (
              <div className="p-20 text-center">
                <div className="inline-flex flex-col items-center gap-4">
                  <div className="w-10 h-10 border-4 border-indigo-50 border-t-indigo-500 rounded-full animate-spin" />
                  <p className="text-gray-400 font-bold text-xs uppercase tracking-widest">Hydrating permissions matrix...</p>
                </div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm text-gray-700 min-w-[800px]">
                  <thead>
                    <tr className="bg-gray-50/50 border-b border-gray-200 font-bold text-gray-400 text-[0.7rem] uppercase tracking-[0.15em]">
                      <th className="px-6 py-5">Security Identifier</th>
                      <th className="px-6 py-5">Role Intent / Description</th>
                      <th className="px-6 py-5">Operational Status</th>
                      <th className="px-6 py-5">Source Type</th>
                      <th className="px-6 py-5 text-right w-24">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {roles.map(r => (
                      <tr key={r.id} className="hover:bg-gray-50/50 transition-colors group">
                        <td className="px-6 py-5">
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${r.is_system_role ? 'bg-gray-900 text-white' : 'bg-indigo-50 text-indigo-600 group-hover:bg-white'}`}>
                              {r.is_system_role ? <Cpu className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
                            </div>
                            <span className="font-bold text-gray-900">{r.name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-5">
                          <div className="text-[0.8125rem] text-gray-500 font-medium leading-relaxed max-w-xs">{r.description || 'No description provided.'}</div>
                        </td>
                        <td className="px-6 py-5">
                          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[0.65rem] font-bold uppercase tracking-widest border ${r.is_active ? 'bg-emerald-50 text-emerald-700 border-emerald-100' : 'bg-gray-50 text-gray-500 border-gray-100'}`}>
                            <div className={`w-1.5 h-1.5 rounded-full ${r.is_active ? 'bg-emerald-500' : 'bg-gray-400'}`} />
                            {r.is_active ? 'Enabled' : 'Disabled'}
                          </span>
                        </td>
                        <td className="px-6 py-5">
                          {r.is_system_role ? (
                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[0.6rem] font-black uppercase tracking-tighter bg-gray-900 text-white">
                              Immutable
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[0.6rem] font-black uppercase tracking-tighter bg-indigo-50 text-indigo-600 border border-indigo-100">
                              Custom
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-5 text-right relative">
                          <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto transition-all translate-x-1 group-hover:translate-x-0">
                            <button 
                              className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all" 
                              onClick={() => handleEdit(r)}
                              title="Modify Role"
                            >
                              <Pencil className="w-4 h-4" />
                            </button>
                            {!r.is_system_role && (
                              <button 
                                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all" 
                                onClick={() => handleDelete(r.id, r.name)}
                                title="Purge Role"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                          <MoreVertical className="w-4 h-4 text-gray-300 ml-auto group-hover:hidden" />
                        </td>
                      </tr>
                    ))}
                    {roles.length === 0 && (
                      <tr>
                        <td colSpan="5" className="text-center py-20">
                          <div className="flex flex-col items-center gap-4 text-gray-300">
                            <ShieldAlert className="w-12 h-12" strokeWidth={1} />
                            <p className="font-bold text-gray-900">Security Matrix Empty</p>
                            <p className="text-sm max-w-xs text-gray-500 leading-relaxed">No access control roles have been defined in the system yet.</p>
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
            <RoleFormModal 
              role={selectedRole} 
              onClose={() => setShowModal(false)} 
              onSave={handleSave} 
            />
          )}
        </div>
      </main>
    </div>
  );
}
