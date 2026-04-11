import { useState, useEffect } from 'react';
import api from '../../api/client';

export default function AdminRolesWidget({ widget }) {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/roles/')
      .then(({ data }) => setRoles(data))
      .catch(() => setRoles([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.02)] font-sans h-full flex flex-col">
      <div className="px-5 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
        <h3 className="m-0 text-[1.05rem] font-bold text-gray-900">{widget.display_name}</h3>
        <span className="bg-gray-800 text-white px-2.5 py-0.5 rounded-full text-[0.6875rem] font-bold uppercase tracking-wider">Admin</span>
      </div>
      {loading ? (
        <div className="flex-1 flex items-center justify-center text-sm text-gray-500 p-8">Loading roles...</div>
      ) : (
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
          {roles.map((role) => (
            <div key={role.id} className={`p-4 rounded-lg border ${role.is_system_role ? 'bg-gray-50/80 border-gray-300' : 'bg-white border-gray-100'}`}>
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                <span className="font-semibold text-gray-900 text-sm tracking-tight">{role.name}</span>
                {role.is_system_role && <span className="text-[0.65rem] font-bold uppercase tracking-wider bg-gray-800 text-white px-1.5 py-0.5 rounded border border-gray-900">System</span>}
                <span className={`text-[0.65rem] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${role.is_active ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-gray-50 text-gray-500 border-gray-200'}`}>
                  {role.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <p className="text-xs text-gray-500 mb-3 leading-relaxed">{role.description}</p>
              <div className="flex flex-wrap gap-1.5">
                {role.permissions.map((p) => (
                  <span key={p.id} className="text-[0.65rem] bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full whitespace-nowrap">{p.name}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
