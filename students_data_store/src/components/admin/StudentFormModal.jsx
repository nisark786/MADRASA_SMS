import { useState } from 'react';
import api from '../../api/client';
import { 
  X, 
  Plus, 
  Trash2, 
  GraduationCap, 
  Check, 
  BookOpen, 
  MapPin, 
  Calendar, 
  FileText,
  Phone,
  User
} from 'lucide-react';

export default function StudentFormModal({ student, onClose, onSaved }) {
  const [formData, setFormData] = useState({
    first_name: student?.first_name || '',
    last_name: student?.last_name || '',
    email: student?.email || '',
    class_name: student?.class_name || '',
    roll_no: student?.roll_no || '',
    admission_no: student?.admission_no || '',
    mobile_numbers: student?.mobile_numbers?.length ? student.mobile_numbers.map(n => ({ value: n })) : [{ value: '' }],
    address: student?.address || '',
    city: student?.city || '',
    state: student?.state || '',
    zip_code: student?.zip_code || '',
    date_of_birth: student?.date_of_birth || '',
    enrollment_date: student?.enrollment_date?.split('T')[0] || new Date().toISOString().split('T')[0],
    notes: student?.notes || '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAddMobile = () => {
    setFormData(prev => ({
      ...prev,
      mobile_numbers: [...prev.mobile_numbers, { value: '' }]
    }));
  };

  const handleRemoveMobile = (index) => {
    setFormData(prev => ({
      ...prev,
      mobile_numbers: prev.mobile_numbers.filter((_, i) => i !== index)
    }));
  };

  const handleMobileChange = (index, val) => {
    const updated = [...formData.mobile_numbers];
    updated[index].value = val;
    setFormData({ ...formData, mobile_numbers: updated });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const payload = {
      ...formData,
      mobile_numbers: formData.mobile_numbers.map(m => m.value).filter(val => val.trim() !== '')
    };

    try {
      if (student) {
        await api.patch(`/students/${student.id}`, payload);
      } else {
        await api.post('/students/', payload);
      }
      onSaved();
      onClose();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'An error occurred while saving.');
    } finally {
      setLoading(false);
    }
  };

  const inputClass = "w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm text-gray-900 outline-none transition-all mt-1.5 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/5 placeholder:text-gray-400 bg-gray-50/50 focus:bg-white";
  const labelClass = "block text-[0.75rem] font-bold text-gray-500 uppercase tracking-widest ml-1";

  return (
    <div className="fixed inset-0 bg-gray-900/60 flex items-center justify-center z-50 p-4 font-sans backdrop-blur-md" onClick={onClose}>
      <div 
        className="bg-white rounded-3xl w-full max-w-[700px] max-h-[90vh] overflow-y-auto shadow-[0_20px_50px_rgba(0,0,0,0.2)] flex flex-col relative" 
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-8 py-6 border-b border-gray-100 flex justify-between items-center bg-white sticky top-0 z-10 shrink-0">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600 p-2 rounded-xl">
              <GraduationCap className="w-5 h-5 text-white" />
            </div>
            <h4 className="m-0 text-xl font-bold text-gray-900 tracking-tight">{student ? 'Modify Student Profile' : 'Register New Student'}</h4>
          </div>
          <button 
            className="text-gray-400 hover:text-gray-900 cursor-pointer w-10 h-10 flex items-center justify-center rounded-2xl hover:bg-gray-100 transition-all active:scale-90 border-none bg-transparent" 
            onClick={onClose}
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="flex flex-col">
          <div className="p-8 flex flex-col gap-8">
            
            {error && (
              <div className="p-4 bg-red-50 text-red-700 text-sm font-bold rounded-2xl border border-red-100 animate-in fade-in slide-in-from-top-2">
                {error}
              </div>
            )}

            <div className="flex flex-col gap-6">
              <h5 className="m-0 text-[0.85rem] font-black text-indigo-600 uppercase tracking-[0.2em] flex items-center gap-2">
                <User className="w-4 h-4" /> Personal Information
              </h5>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className={labelClass}>First Name *</label>
                  <input type="text" required value={formData.first_name} onChange={(e) => setFormData({ ...formData, first_name: e.target.value })} className={inputClass} placeholder="e.g. John" />
                </div>
                <div>
                  <label className={labelClass}>Last Name *</label>
                  <input type="text" required value={formData.last_name} onChange={(e) => setFormData({ ...formData, last_name: e.target.value })} className={inputClass} placeholder="e.g. Doe" />
                </div>
              </div>
              <div>
                <label className={labelClass}>Email Address *</label>
                <input type="email" required value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} className={inputClass} placeholder="john.doe@university.edu" />
              </div>
            </div>

            <div className="p-6 bg-indigo-50/30 rounded-3xl border border-indigo-100/50 flex flex-col gap-6">
              <h5 className="m-0 text-[0.85rem] font-black text-indigo-600 uppercase tracking-[0.2em] flex items-center gap-2">
                <BookOpen className="w-4 h-4" /> Academic Records
              </h5>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div>
                  <label className={labelClass}>Current Class</label>
                  <input type="text" value={formData.class_name} onChange={(e) => setFormData({ ...formData, class_name: e.target.value })} className={inputClass} placeholder="e.g. 12-B" />
                </div>
                <div>
                  <label className={labelClass}>Roll Number</label>
                  <input type="text" value={formData.roll_no} onChange={(e) => setFormData({ ...formData, roll_no: e.target.value })} className={inputClass} placeholder="e.g. 042" />
                </div>
                <div>
                  <label className={labelClass}>Admission No.</label>
                  <input type="text" value={formData.admission_no} onChange={(e) => setFormData({ ...formData, admission_no: e.target.value })} className={inputClass} placeholder="ADM-2024-01" />
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-4">
              <div className="flex justify-between items-center">
                <h5 className="m-0 text-[0.85rem] font-black text-indigo-600 uppercase tracking-[0.2em] flex items-center gap-2">
                  <Phone className="w-4 h-4" /> Contact Numbers
                </h5>
                <button 
                  type="button" 
                  onClick={handleAddMobile}
                  className="text-[0.7rem] text-indigo-600 font-bold uppercase tracking-widest hover:bg-indigo-100 px-3 py-1.5 rounded-xl border border-indigo-100 transition-all flex items-center gap-1.5 active:scale-95 bg-white"
                >
                  <Plus className="w-3 h-3" strokeWidth={3} /> Add More
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {formData.mobile_numbers.map((mobile, index) => (
                  <div key={index} className="flex gap-2 items-center group">
                    <div className="relative flex-1">
                      <input 
                        type="tel" 
                        value={mobile.value} 
                        onChange={(e) => handleMobileChange(index, e.target.value)} 
                        className={inputClass} 
                        style={{ marginTop: 0 }}
                        placeholder="Mobile number" 
                      />
                    </div>
                    {formData.mobile_numbers.length > 1 && (
                      <button 
                        type="button"
                        onClick={() => handleRemoveMobile(index)}
                        className="p-2.5 text-gray-300 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all"
                        title="Remove entry"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex flex-col gap-6">
              <h5 className="m-0 text-[0.85rem] font-black text-indigo-600 uppercase tracking-[0.2em] flex items-center gap-2">
                <MapPin className="w-4 h-4" /> Residential Details
              </h5>
              <div>
                <label className={labelClass}>Street Address</label>
                <input type="text" value={formData.address} onChange={(e) => setFormData({ ...formData, address: e.target.value })} className={inputClass} placeholder="Building, Street, Area" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div>
                  <label className={labelClass}>City</label>
                  <input type="text" value={formData.city} onChange={(e) => setFormData({ ...formData, city: e.target.value })} className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>State</label>
                  <input type="text" value={formData.state} onChange={(e) => setFormData({ ...formData, state: e.target.value })} className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>Postal Code</label>
                  <input type="text" value={formData.zip_code} onChange={(e) => setFormData({ ...formData, zip_code: e.target.value })} className={inputClass} />
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-6">
              <h5 className="m-0 text-[0.85rem] font-black text-indigo-600 uppercase tracking-[0.2em] flex items-center gap-2">
                <Calendar className="w-4 h-4" /> Key Dates
              </h5>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className={labelClass}>Date of Birth</label>
                  <input type="date" value={formData.date_of_birth} onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })} className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>Official Enrollment</label>
                  <input type="date" value={formData.enrollment_date} onChange={(e) => setFormData({ ...formData, enrollment_date: e.target.value })} className={inputClass} />
                </div>
              </div>
            </div>

            <div>
              <h5 className="mb-3 text-[0.85rem] font-black text-indigo-600 uppercase tracking-[0.2em] flex items-center gap-2">
                <FileText className="w-4 h-4" /> Additional Notes
              </h5>
              <textarea value={formData.notes} onChange={(e) => setFormData({ ...formData, notes: e.target.value })} rows="3" className={`${inputClass} min-h-[100px] resize-none py-3`} placeholder="Mention medical history, scholarship details, or behavioral notes..." />
            </div>
            
          </div>
          
          <div className="px-8 py-6 border-t border-gray-100 flex justify-end gap-3 bg-white sticky bottom-0 z-10 shrink-0">
            <button 
              type="button" 
              className="px-6 py-2.5 rounded-xl text-sm font-bold text-gray-500 bg-gray-50 hover:bg-gray-100 transition-all border-none active:scale-95" 
              onClick={onClose}
              disabled={loading}
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
              {student ? 'Update Database' : 'Finalize Registration'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
