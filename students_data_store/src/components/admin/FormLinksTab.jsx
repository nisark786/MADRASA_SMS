import { useState, useEffect } from 'react';
import api from '../../api/client';
import { 
  Link as LinkIcon, 
  Plus, 
  Trash2, 
  Power,
  Copy,
  MessageCircle,
  Share2
} from 'lucide-react';

const AVAILABLE_FIELDS = [
  { name: 'first_name', label: 'First Name', type: 'text', required: true },
  { name: 'last_name', label: 'Last Name', type: 'text', required: true },
  { name: 'email', label: 'Email', type: 'email', required: true },
  { name: 'class_name', label: 'Class/Grade', type: 'text', required: false },
  { name: 'roll_no', label: 'Roll No', type: 'text', required: false },
  { name: 'admission_no', label: 'Admission No', type: 'text', required: false },
  { name: 'mobile_numbers', label: 'Mobile Number', type: 'text', required: false },
  { name: 'address', label: 'Address', type: 'text', required: false },
  { name: 'city', label: 'City', type: 'text', required: false },
  { name: 'state', label: 'State', type: 'text', required: false },
  { name: 'zip_code', label: 'Zip Code', type: 'text', required: false },
  { name: 'date_of_birth', label: 'Date of Birth', type: 'date', required: false },
];

export default function FormLinksTab() {
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [selectedFields, setSelectedFields] = useState(['first_name', 'last_name', 'email']);

  const loadLinks = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/forms/');
      setLinks(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLinks();
  }, []);

  const handleCreate = async () => {
    if (!newTitle) return alert('Please provide a form title');
    const allowed_fields = AVAILABLE_FIELDS.filter(f => selectedFields.includes(f.name));
    
    try {
      await api.post('/forms/', { title: newTitle, allowed_fields });
      setShowModal(false);
      setNewTitle('');
      setSelectedFields(['first_name', 'last_name', 'email']);
      loadLinks();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create form');
    }
  };

  const toggleStatus = async (link) => {
    try {
      await api.patch(`/forms/${link.id}/status`, { is_active: !link.is_active });
      loadLinks();
    } catch (err) {
      alert('Failed to toggle status');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this form link permanently?')) return;
    try {
      await api.delete(`/forms/${id}`);
      loadLinks();
    } catch (err) {
      alert('Failed to delete');
    }
  };

  const handleCopy = (token) => {
    const url = `${window.location.origin}/form/${token}`;
    navigator.clipboard.writeText(url);
    alert('Link copied to clipboard!');
  };

  const handleWhatsApp = (token) => {
    const url = `${window.location.origin}/form/${token}`;
    window.open(`https://wa.me/?text=Please fill out this admission form: ${encodeURIComponent(url)}`, '_blank');
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Manage Form Links</h2>
          <p className="text-sm text-gray-500">Generate secure, unique admission links to share with students.</p>
        </div>
        <button 
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-xl font-bold hover:bg-indigo-700"
        >
          <Plus className="w-4 h-4" />
          Create New Link
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full py-12 text-center text-gray-400">Loading links...</div>
        ) : links.length === 0 ? (
          <div className="col-span-full py-12 text-center text-gray-400 flex flex-col items-center">
            <LinkIcon className="w-12 h-12 mb-2 text-gray-300" />
            <p>No form links created yet.</p>
          </div>
        ) : (
          links.map(link => {
            const publicUrl = `${window.location.origin}/form/${link.token}`;
            return (
              <div key={link.id} className={`bg-white rounded-2xl border ${link.is_active ? 'border-indigo-100 shadow-sm' : 'border-gray-200 opacity-75'} p-6 flex flex-col`}>
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-bold text-gray-900 line-clamp-1">{link.title}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-[0.65rem] uppercase font-black px-2 py-0.5 rounded-full ${link.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {link.is_active ? 'Active' : 'Blocked'}
                      </span>
                      <span className="text-xs text-gray-400 font-mono">{link.token}</span>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <button onClick={() => toggleStatus(link)} className="p-1.5 text-gray-400 hover:text-indigo-600 rounded-lg hover:bg-gray-100" title={link.is_active ? 'Block Link' : 'Activate Link'}>
                      <Power className="w-4 h-4" />
                    </button>
                    <button onClick={() => handleDelete(link.id)} className="p-1.5 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50" title="Delete">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="text-xs text-gray-500 mb-6 flex-1">
                  <strong>Fields included: </strong>
                  <span className="line-clamp-2 mt-1">
                    {link.allowed_fields.map(f => f.label).join(', ')}
                  </span>
                </div>

                {link.is_active && (
                  <div className="flex flex-wrap gap-2 pt-4 border-t border-gray-100">
                    <button 
                      onClick={() => handleCopy(link.token)}
                      className="flex-1 min-w-[100px] flex items-center justify-center gap-1.5 py-2 bg-gray-100/80 hover:bg-gray-200 text-gray-700 text-xs font-bold rounded-xl transition-colors"
                    >
                      <Copy className="w-3.5 h-3.5" /> Copy
                    </button>
                    <button 
                      onClick={() => handleWhatsApp(link.token)}
                      className="flex-1 min-w-[100px] flex items-center justify-center gap-1.5 py-2 bg-[#25D366]/10 hover:bg-[#25D366]/20 text-[#25D366] text-xs font-bold rounded-xl transition-colors"
                    >
                      <MessageCircle className="w-3.5 h-3.5" /> WhatsApp
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 backdrop-blur-sm">
          <div className="bg-white w-full max-w-lg rounded-3xl p-8 shadow-2xl">
            <h2 className="text-xl font-bold mb-6">Create Form Link</h2>
            
            <div className="mb-4">
              <label className="block text-sm font-bold text-gray-700 mb-1">Form Title</label>
              <input 
                type="text" 
                value={newTitle}
                onChange={e => setNewTitle(e.target.value)}
                placeholder="e.g. Grade 10 Admission 2024"
                className="w-full border border-gray-200 rounded-xl px-4 py-2 outline-none focus:border-indigo-500 text-sm"
              />
            </div>

            <div className="mb-8">
              <label className="block text-sm font-bold text-gray-700 mb-2">Select Visible Fields</label>
              <div className="grid grid-cols-2 gap-3 max-h-60 overflow-y-auto p-1">
                {AVAILABLE_FIELDS.map(f => (
                  <label key={f.name} className={`flex items-center gap-2 p-2 rounded-lg border cursor-pointer transition-colors ${selectedFields.includes(f.name) ? 'bg-indigo-50 border-indigo-200' : 'bg-white border-gray-100 hover:border-gray-200'}`}>
                    <input 
                      type="checkbox"
                      checked={selectedFields.includes(f.name)}
                      onChange={(e) => {
                        if (['first_name', 'last_name', 'email'].includes(f.name)) return; // always required
                        if (e.target.checked) setSelectedFields([...selectedFields, f.name]);
                        else setSelectedFields(selectedFields.filter(x => x !== f.name));
                      }}
                      disabled={['first_name', 'last_name', 'email'].includes(f.name)}
                      className="rounded text-indigo-600 focus:ring-0 cursor-pointer"
                    />
                    <span className="text-xs font-bold text-gray-700">{f.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex gap-3 justify-end mt-4 pt-4 border-t border-gray-100">
              <button onClick={() => setShowModal(false)} className="px-5 py-2 text-sm font-bold text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-xl">Cancel</button>
              <button onClick={handleCreate} className="px-5 py-2 text-sm font-bold bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-lg shadow-indigo-200">
                Generate Link
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
