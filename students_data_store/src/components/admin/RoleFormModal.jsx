import { useState, useEffect } from 'react';
import api from '../../api/client';
import { 
  X, 
  ShieldCheck, 
  ShieldAlert, 
  Check, 
  Plus, 
  Shield, 
  Info,
  Lock,
  Eye
} from 'lucide-react';

export default function RoleFormModal({ role, onClose, onSave }) {
  const isEditing = !!role;
  const [formData, setFormData] = useState({
    name: role?.name || '',
    description: role?.description || '',
    is_active: role !== undefined ? role?.is_active : true,
    permission_ids: role?.permissions?.map(p => p.id) || []
  });

  const [availablePermissions, setAvailablePermissions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/permissions/')
      .then(({ data }) => setAvailablePermissions(data))
      .catch((err) => console.error("Failed to load permissions", err));
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    if (type === 'checkbox') {
      if (name === 'is_active') {
        setFormData(prev => ({ ...prev, is_active: checked }));
      } else {
        setFormData(prev => {
          const newPerms = checked 
            ? [...prev.permission_ids, value] 
            : prev.permission_ids.filter(id => id !== value);
          return { ...prev, permission_ids: newPerms };
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
        await api.patch(`/roles/${role.id}`, {
          description: formData.description,
          is_active: formData.is_active,
          permission_ids: formData.permission_ids
        });
      } else {
        await api.post('/roles/', {
          name: formData.name,
          description: formData.description,
          permission_ids: formData.permission_ids
        });
      }
      onSave(); // trigger refresh
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Operation failed. Verify system connectivity.');
    } finally {
      setLoading(false);
    }
  };

  const labelClass = "text-[0.75rem] font-bold text-gray-500 uppercase tracking-widest ml-1";
  const inputClass = "w-full px-4 py-2.5 bg-gray-50/50 border border-gray-200 rounded-xl text-sm text-gray-900 outline-none transition-all placeholder:text-gray-400 focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/5";

  return (
    <div className="fixed inset-0 bg-gray-900/60 flex items-center justify-center z-50 p-4 font-sans backdrop-blur-md" onClick={onClose}>
      <div 
        className="bg-white rounded-3xl w-full max-w-[520px] max-h-[90vh] overflow-y-auto shadow-[0_20px_50px_rgba(0,0,0,0.2)] flex flex-col relative" 
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-8 py-6 border-b border-gray-100 flex justify-between items-center bg-white sticky top-0 z-10 shrink-0">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600 p-2 rounded-xl">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <h3 className="m-0 text-xl font-bold text-gray-900 tracking-tight">{isEditing ? 'Modify Security Role' : 'Initialize New Role'}</h3>
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
                <ShieldAlert className="w-5 h-5 shrink-0" />
                <span>{error}</span>
              </div>
            )}
            
            <div className="flex flex-col gap-2">
              <label className={labelClass}>Role Identifier {!isEditing && '*'}</label>
              <div className="relative group">
                <Lock className={`absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors ${isEditing ? 'text-gray-300' : 'text-gray-400 group-focus-within:text-indigo-500'}`} />
                <input 
                  type="text" 
                  name="name" 
                  placeholder="e.g. academic_auditor"
                  value={formData.name} 
                  onChange={handleChange} 
                  disabled={isEditing} 
                  required={!isEditing} 
                  className={`${inputClass} pl-10 disabled:bg-gray-100 disabled:text-gray-400 disabled:border-gray-200 cursor-not-allowed`}
                />
              </div>
              {isEditing && (
                <div className="flex items-center gap-1.5 ml-1 mt-1">
                  <Info className="w-3 h-3 text-gray-400" />
                  <span className="text-[0.65rem] font-bold text-gray-400 uppercase tracking-tighter">Canonical identifiers are immutable</span>
                </div>
              )}
            </div>

            <div className="flex flex-col gap-2">
              <label className={labelClass}>Functional Description</label>
              <textarea 
                name="description" 
                placeholder="Explain the purpose and scope of this role..."
                value={formData.description} 
                onChange={handleChange} 
                className={`${inputClass} min-h-[80px] py-3 resize-none`}
              />
            </div>

            {isEditing && !role.is_system_role && (
              <div className="bg-gray-50/50 p-4 rounded-2xl border border-gray-100">
                <label className="flex items-center gap-3 font-bold text-gray-700 cursor-pointer text-sm">
                  <div className="relative flex items-center">
                    <input className="peer h-5 w-5 cursor-pointer appearance-none rounded-md border border-gray-300 transition-all checked:border-indigo-600 checked:bg-indigo-600 focus:outline-none" type="checkbox" name="is_active" checked={formData.is_active} onChange={handleChange} />
                    <Check className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white opacity-0 peer-checked:opacity-100 transition-opacity" strokeWidth={4} />
                  </div>
                  Role is currently active and assignable
                </label>
              </div>
            )}

            <div className="flex flex-col gap-4 pt-4 border-t border-gray-100">
              <div className="flex justify-between items-end">
                <label className={labelClass}>Resource Permissions</label>
                <span className="text-[0.65rem] font-black text-indigo-600 uppercase tracking-widest bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-100">
                  {formData.permission_ids.length} Selected
                </span>
              </div>
              <div className="grid grid-cols-1 gap-2 max-h-[220px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-200">
                {availablePermissions.map(perm => (
                  <label key={perm.id} className="flex items-start justify-between gap-3 p-3 bg-white border border-gray-100 rounded-2xl cursor-pointer hover:border-indigo-200 hover:bg-indigo-50/20 transition-all group/perm">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-lg bg-gray-50 text-gray-400 flex items-center justify-center shrink-0 group-hover/perm:bg-white group-hover/perm:text-indigo-600 transition-colors mt-0.5">
                        <Eye className="w-4 h-4" />
                      </div>
                      <div className="flex flex-col">
                        <span className="text-sm font-bold text-gray-900 group-hover/perm:text-indigo-600 transition-colors">{perm.name}</span>
                        <span className="text-[0.7rem] text-gray-400 font-medium leading-tight">{perm.description}</span>
                      </div>
                    </div>
                    <div className="relative flex items-center pt-1">
                      <input 
                        type="checkbox" 
                        name="permission_ids" 
                        value={perm.id} 
                        checked={formData.permission_ids.includes(perm.id)}
                        onChange={handleChange}
                        className="peer h-5 w-5 cursor-pointer appearance-none rounded-md border border-gray-300 transition-all checked:border-indigo-600 checked:bg-indigo-600 focus:outline-none"
                      />
                      <Check className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white opacity-0 peer-checked:opacity-100 transition-opacity" strokeWidth={4} />
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
              Discard
            </button>
            <button 
              type="submit" 
              className="px-8 py-2.5 rounded-xl text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 disabled:opacity-70 disabled:cursor-not-allowed flex items-center gap-2.5 active:scale-95 border-none"
              disabled={loading}
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : <Check className="w-4 h-4" strokeWidth={3} />}
              {isEditing ? 'Commit Overrides' : 'Authorize Role'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
