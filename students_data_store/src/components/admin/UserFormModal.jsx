import { useState, useEffect } from 'react';
import api from '../../api/client';
import { 
  X, 
  User, 
  Mail, 
  Lock, 
  Shield, 
  Check, 
  Users,
  AlertCircle
} from 'lucide-react';

export default function UserFormModal({ user, onClose, onSave }) {
  const isEditing = !!user;
  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    password: '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    is_active: user !== undefined ? user?.is_active : true,
    role_ids: []
  });

  const [availableRoles, setAvailableRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/roles/')
      .then(({ data }) => setAvailableRoles(data))
      .catch((err) => console.error("Failed to load roles", err));
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    if (type === 'checkbox') {
      if (name === 'is_active') {
        setFormData(prev => ({ ...prev, is_active: checked }));
      } else {
        setFormData(prev => {
          const newRoles = checked 
            ? [...prev.role_ids, value] 
            : prev.role_ids.filter(id => id !== value);
          return { ...prev, role_ids: newRoles };
        });
      }
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isEditing) {
        const payload = {
          first_name: formData.first_name,
          last_name: formData.last_name,
          is_active: formData.is_active,
        };
        if (formData.role_ids.length > 0) {
          payload.role_ids = formData.role_ids;
        }
        await api.patch(`/users/${user.id}`, payload);
      } else {
        if (!formData.password) {
          throw new Error("A secure password is required for new accounts.");
        }
        await api.post('/users/', formData);
      }
      onSave();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Transmission error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const inputGroupClass = "flex flex-col gap-2";
  const labelClass = "text-[0.75rem] font-bold text-gray-500 uppercase tracking-widest ml-1";
  const inputClass = "w-full pl-10 pr-4 py-2.5 bg-gray-50/50 border border-gray-200 rounded-xl text-sm text-gray-900 outline-none transition-all placeholder:text-gray-400 focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/5";
  const iconClass = "absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-indigo-500 transition-colors";

  return (
    <div className="fixed inset-0 bg-gray-900/60 flex items-center justify-center z-50 p-4 font-sans backdrop-blur-md" onClick={onClose}>
      <div 
        className="bg-white rounded-3xl w-full max-w-[520px] max-h-[90vh] overflow-y-auto shadow-[0_20px_50px_rgba(0,0,0,0.2)] flex flex-col relative" 
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-8 py-6 border-b border-gray-100 flex justify-between items-center bg-white sticky top-0 z-10 shrink-0">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600 p-2 rounded-xl">
              <Users className="w-5 h-5 text-white" />
            </div>
            <h3 className="m-0 text-xl font-bold text-gray-900 tracking-tight">{isEditing ? 'Modify User Profile' : 'Provision New Account'}</h3>
          </div>
          <button 
            className="text-gray-400 hover:text-gray-900 cursor-pointer w-10 h-10 flex items-center justify-center rounded-2xl hover:bg-gray-100 transition-all active:scale-90 border-none bg-transparent" 
            onClick={onClose}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col">
          <div className="p-8 flex flex-col gap-6">
            {error && (
              <div className="flex items-start gap-3 p-4 bg-red-50 text-red-700 text-sm font-bold rounded-2xl border border-red-100 animate-in fade-in slide-in-from-top-2">
                <AlertCircle className="w-5 h-5 shrink-0" />
                <span>{error}</span>
              </div>
            )}
            
            {!isEditing && (
              <>
                <div className={inputGroupClass}>
                  <label className={labelClass}>Unique Username</label>
                  <div className="relative group">
                    <User className={iconClass} />
                    <input className={inputClass} type="text" name="username" placeholder="e.g. jdoe_admin" value={formData.username} onChange={handleChange} required />
                  </div>
                </div>
                <div className={inputGroupClass}>
                  <label className={labelClass}>Email Address</label>
                  <div className="relative group">
                    <Mail className={iconClass} />
                    <input className={inputClass} type="email" name="email" placeholder="j.doe@example.com" value={formData.email} onChange={handleChange} required />
                  </div>
                </div>
                <div className={inputGroupClass}>
                  <label className={labelClass}>Initial Password</label>
                  <div className="relative group">
                    <Lock className={iconClass} />
                    <input className={inputClass} type="password" name="password" placeholder="••••••••" value={formData.password} onChange={handleChange} required={!isEditing} />
                  </div>
                </div>
              </>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className={inputGroupClass}>
                <label className={labelClass}>First Name</label>
                <input className="w-full px-4 py-2.5 bg-gray-50/50 border border-gray-200 rounded-xl text-sm outline-none focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/5 transition-all" type="text" name="first_name" placeholder="John" value={formData.first_name} onChange={handleChange} />
              </div>
              <div className={inputGroupClass}>
                <label className={labelClass}>Last Name</label>
                <input className="w-full px-4 py-2.5 bg-gray-50/50 border border-gray-200 rounded-xl text-sm outline-none focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/5 transition-all" type="text" name="last_name" placeholder="Doe" value={formData.last_name} onChange={handleChange} />
              </div>
            </div>

            {isEditing && (
              <div className="bg-gray-50/50 p-4 rounded-2xl border border-gray-100">
                <label className="flex items-center gap-3 font-bold text-gray-700 cursor-pointer text-sm">
                  <div className="relative flex items-center">
                    <input className="peer h-5 w-5 cursor-pointer appearance-none rounded-md border border-gray-300 transition-all checked:border-indigo-600 checked:bg-indigo-600 focus:outline-none" type="checkbox" name="is_active" checked={formData.is_active} onChange={handleChange} />
                    <Check className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white opacity-0 peer-checked:opacity-100 transition-opacity" strokeWidth={4} />
                  </div>
                  User account is currently active
                </label>
              </div>
            )}

            <div className="flex flex-col gap-4 pt-4 border-t border-gray-100">
              <div className="flex justify-between items-end">
                <label className={labelClass}>Role Enrollment</label>
                {isEditing && <span className="text-[0.65rem] font-black text-gray-300 uppercase tracking-tighter italic">Merge with existing</span>}
              </div>
              <div className="grid grid-cols-1 gap-2 max-h-[180px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-200">
                {availableRoles.map(role => (
                  <label key={role.id} className="flex items-center justify-between gap-3 p-3 bg-white border border-gray-100 rounded-2xl cursor-pointer hover:border-indigo-200 hover:bg-indigo-50/20 transition-all group/role">
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${role.is_system_role ? 'bg-gray-900 text-white' : 'bg-indigo-50 text-indigo-600'}`}>
                        <Shield className="w-4 h-4" />
                      </div>
                      <div className="flex flex-col">
                        <span className="text-sm font-bold text-gray-900">{role.name}</span>
                        {role.is_system_role && <span className="text-[0.65rem] font-bold text-gray-400 uppercase tracking-tighter italic">Critical System Role</span>}
                      </div>
                    </div>
                    <div className="relative flex items-center">
                      <input 
                        type="checkbox" 
                        name="role_ids" 
                        value={role.id} 
                        checked={formData.role_ids.includes(role.id)}
                        onChange={handleChange}
                        className="peer h-5 w-5 cursor-pointer appearance-none rounded-full border border-gray-300 transition-all checked:border-indigo-600 checked:bg-indigo-600 focus:outline-none"
                      />
                      <Check className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 text-white opacity-0 peer-checked:opacity-100 transition-opacity" strokeWidth={4} />
                    </div>
                  </label>
                ))}
              </div>
            </div>

          </div>
          <div className="px-8 py-6 border-t border-gray-100 flex justify-end gap-3 bg-white sticky bottom-0 z-10 shrink-0">
            <button 
              type="button" 
              className="px-6 py-2.5 rounded-xl text-sm font-bold text-gray-500 bg-gray-50 hover:bg-gray-100 transition-all border-none active:scale-95" 
              onClick={onClose}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="px-8 py-2.5 rounded-xl text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 disabled:opacity-70 disabled:cursor-not-allowed flex items-center gap-2.5 active:scale-95 border-none"
              disabled={loading}
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : <Check className="w-4 h-4" strokeWidth={3} />}
              {isEditing ? 'Commit Changes' : 'Finalize Account'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
