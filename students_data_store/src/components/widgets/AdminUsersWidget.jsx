import { useState, useEffect } from 'react';
import api from '../../api/client';

export default function AdminUsersWidget({ widget }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/users/')
      .then(({ data }) => setUsers(data))
      .catch(() => setUsers([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.02)] font-sans h-full flex flex-col">
      <div className="px-5 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
        <h3 className="m-0 text-[1.05rem] font-bold text-gray-900">{widget.display_name}</h3>
        <span className="bg-gray-800 text-white px-2.5 py-0.5 rounded-full text-[0.6875rem] font-bold uppercase tracking-wider">Admin</span>
      </div>
      {loading ? (
        <div className="flex-1 flex items-center justify-center text-sm text-gray-500 p-8">Loading users...</div>
      ) : (
        <div className="flex-1 overflow-x-auto overflow-y-auto">
          <table className="w-full text-left border-collapse text-sm text-gray-700 min-w-[400px]">
            <thead className="bg-gray-50/80 sticky top-0 border-b border-gray-200">
              <tr className="text-[0.7rem] uppercase tracking-wider text-gray-500 font-semibold">
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Last Login</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-4 py-3 text-gray-900 font-medium">{u.first_name} {u.last_name}</td>
                  <td className="px-4 py-3 text-gray-500">{u.email}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-1.5 py-0.5 rounded text-[0.65rem] font-bold uppercase tracking-wider border ${u.is_active ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-gray-50 text-gray-500 border-gray-200'}`}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {u.last_login ? new Date(u.last_login).toLocaleDateString() : 'Never'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
