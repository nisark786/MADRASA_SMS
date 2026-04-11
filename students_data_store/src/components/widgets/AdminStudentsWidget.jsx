import { useState, useEffect } from 'react';
import api from '../../api/client';

export default function AdminStudentsWidget({ widget }) {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({
    first_name: '', last_name: '', email: '', phone: '', address: '',
    city: '', state: '', zip_code: '', date_of_birth: '',
    enrollment_date: new Date().toISOString().split('T')[0], notes: '',
  });

  const loadStudents = async () => {
    try {
      setLoading(true);
      const { data } = await api.get('/students/');
      setStudents(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load students:', err);
      setStudents([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadStudents(); }, []);

  const handleAdd = () => {
    setEditingId(null);
    setFormData({
      first_name: '', last_name: '', email: '', phone: '', address: '',
      city: '', state: '', zip_code: '', date_of_birth: '',
      enrollment_date: new Date().toISOString().split('T')[0], notes: '',
    });
    setShowForm(true);
  };

  const handleEdit = (student) => {
    setEditingId(student.id);
    setFormData({
      first_name: student.first_name, last_name: student.last_name, email: student.email,
      phone: student.phone || '', address: student.address || '', city: student.city || '',
      state: student.state || '', zip_code: student.zip_code || '', date_of_birth: student.date_of_birth || '',
      enrollment_date: student.enrollment_date?.split('T')[0] || '', notes: student.notes || '',
    });
    setShowForm(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) await api.patch(`/students/${editingId}`, formData);
      else await api.post('/students/', formData);
      setShowForm(false);
      loadStudents();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error saving student');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this student?')) return;
    try {
      await api.delete(`/students/${id}`);
      loadStudents();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error deleting student');
    }
  };

  const filteredStudents = students.filter(
    (s) =>
      s.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const inputClass = "w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-gray-900 outline-none transition-all mt-1.5 focus:border-indigo-500 focus:ring-[3px] focus:ring-indigo-500/10 placeholder:text-gray-400";
  const labelClass = "block text-[0.8125rem] font-medium text-gray-700";

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.02)] font-sans h-full flex flex-col relative">
      <div className="px-5 py-4 border-b border-gray-100 flex flex-wrap gap-4 justify-between items-center bg-gray-50/50">
        <h3 className="m-0 text-[1.05rem] font-bold text-gray-900">{widget.display_name}</h3>
        <div className="flex items-center gap-3">
          <button className="px-3.5 py-1.5 bg-indigo-600 text-white rounded-md text-[0.8125rem] font-semibold transition-colors hover:bg-indigo-700 whitespace-nowrap" onClick={handleAdd}>
            ➕ Add Student
          </button>
          <span className="bg-gray-800 text-white px-2.5 py-0.5 rounded-full text-[0.6875rem] font-bold uppercase tracking-wider whitespace-nowrap">
            {students.length} students
          </span>
        </div>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={() => setShowForm(false)}>
          <div className="bg-white rounded-xl w-full max-w-[600px] max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col font-sans" onClick={(e) => e.stopPropagation()}>
            <div className="px-6 py-5 border-b border-gray-200 flex justify-between items-center bg-gray-50/50 sticky top-0 z-10">
              <h4 className="m-0 text-[1.125rem] font-bold text-gray-900">{editingId ? 'Edit Student' : 'Add New Student'}</h4>
              <button className="bg-transparent border-none text-2xl text-gray-400 hover:text-gray-900 cursor-pointer w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-200 transition-colors" onClick={() => setShowForm(false)}>&times;</button>
            </div>
            
            <form onSubmit={handleSubmit} className="flex flex-col">
              <div className="p-6 flex flex-col gap-4.5">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>First Name *</label>
                    <input type="text" required value={formData.first_name} onChange={(e) => setFormData({ ...formData, first_name: e.target.value })} className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>Last Name *</label>
                    <input type="text" required value={formData.last_name} onChange={(e) => setFormData({ ...formData, last_name: e.target.value })} className={inputClass} />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Email *</label>
                    <input type="email" required value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>Phone</label>
                    <input type="tel" value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} className={inputClass} />
                  </div>
                </div>

                <div>
                  <label className={labelClass}>Address</label>
                  <input type="text" value={formData.address} onChange={(e) => setFormData({ ...formData, address: e.target.value })} className={inputClass} />
                </div>

                <div className="grid grid-cols-[2fr_1fr_1fr] gap-4">
                  <div>
                    <label className={labelClass}>City</label>
                    <input type="text" value={formData.city} onChange={(e) => setFormData({ ...formData, city: e.target.value })} className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>State</label>
                    <input type="text" value={formData.state} onChange={(e) => setFormData({ ...formData, state: e.target.value })} className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>Zip Code</label>
                    <input type="text" value={formData.zip_code} onChange={(e) => setFormData({ ...formData, zip_code: e.target.value })} className={inputClass} />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Date of Birth</label>
                    <input type="date" value={formData.date_of_birth} onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })} className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>Enrollment Date</label>
                    <input type="date" value={formData.enrollment_date} onChange={(e) => setFormData({ ...formData, enrollment_date: e.target.value })} className={inputClass} />
                  </div>
                </div>

                <div>
                  <label className={labelClass}>Notes</label>
                  <textarea value={formData.notes} onChange={(e) => setFormData({ ...formData, notes: e.target.value })} rows="3" className={`${inputClass} min-h-[80px] resize-y`} />
                </div>
              </div>
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3 bg-gray-50/50 sticky bottom-0 z-10">
                <button type="button" className="px-4 py-2 rounded-lg text-sm font-semibold text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition-colors" onClick={() => setShowForm(false)}>Cancel</button>
                <button type="submit" className="px-4 py-2 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 transition-colors shadow-sm">{editingId ? 'Update' : 'Create'} Student</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="p-3 border-b border-gray-100 bg-white shrink-0">
        <input
          type="text"
          placeholder="🔍 Search by name or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-3 py-2 border border-gray-200 rounded-md text-[0.8125rem] text-gray-900 outline-none transition-all placeholder:text-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 bg-gray-50/50"
        />
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center text-sm text-gray-500 p-8">Loading students...</div>
      ) : filteredStudents.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-sm text-gray-400 p-8 text-center flex-col gap-2">
          <div className="text-3xl mb-2">📭</div>
          <p>No students found.</p>
          {students.length === 0 && <p>Add one to get started!</p>}
        </div>
      ) : (
        <div className="flex-1 overflow-x-auto overflow-y-auto">
          <table className="w-full text-left border-collapse text-sm text-gray-700 min-w-[600px]">
            <thead className="bg-gray-50/80 sticky top-0 border-b border-gray-200 z-0">
              <tr className="text-[0.7rem] uppercase tracking-wider text-gray-500 font-semibold">
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Phone</th>
                <th className="px-4 py-3">City</th>
                <th className="px-4 py-3 w-[150px]">Source</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredStudents.map((student) => (
                <tr key={student.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-4 py-3 text-gray-900 font-medium whitespace-nowrap">
                    {student.first_name} {student.last_name}
                  </td>
                  <td className="px-4 py-3 text-gray-500 max-w-[200px] truncate" title={student.email}>{student.email}</td>
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{student.phone || '—'}</td>
                  <td className="px-4 py-3 text-gray-500">{student.city || '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded text-[0.6875rem] font-bold tracking-wider border whitespace-nowrap ${student.submitted_via_form ? 'bg-purple-50 text-purple-700 border-purple-200' : 'bg-gray-50 text-gray-600 border-gray-200'}`}>
                      {student.submitted_via_form ? '📋 Form' : '✏️ Manual'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    <button className="px-2 py-1 bg-white hover:bg-gray-50 text-gray-600 border border-gray-200 rounded text-xs mx-0.5 cursor-pointer transition-colors" onClick={() => handleEdit(student)} title="Edit">✏️</button>
                    <button className="px-2 py-1 bg-white hover:bg-red-50 text-red-500 border border-gray-200 rounded text-xs mx-0.5 cursor-pointer transition-colors" onClick={() => handleDelete(student.id)} title="Delete">🗑️</button>
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
