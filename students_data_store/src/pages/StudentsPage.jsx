import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import StudentFormModal from '../components/admin/StudentFormModal';
import Sidebar from '../components/layout/Sidebar';
import FormLinksTab from '../components/admin/FormLinksTab';
import PendingRequestsTab from '../components/admin/PendingRequestsTab';
import ExportConfigModal from '../components/admin/ExportConfigModal';
import { 
  Search, 
  Plus, 
  Pencil, 
  Trash2, 
  GraduationCap, 
  User,
  MoreVertical,
  Users,
  Link as LinkIcon,
  Inbox,
  Download
} from 'lucide-react';

export default function StudentsPage() {
  const [activeTab, setActiveTab] = useState('directory'); // directory | forms | pending
  
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [editingStudent, setEditingStudent] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

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

  useEffect(() => {
    if (activeTab === 'directory') {
      loadStudents();
    }
  }, [activeTab]);

  const handleAdd = () => {
    setEditingStudent(null);
    setShowForm(true);
  };

  const handleEdit = (student) => {
    setEditingStudent(student);
    setShowForm(true);
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

  const filteredStudents = students.filter((s) => {
    const term = searchTerm.toLowerCase();
    const nameStr = `${s.first_name} ${s.last_name}`.toLowerCase();
    return (
      nameStr.includes(term) ||
      (s.email && s.email.toLowerCase().includes(term)) ||
      (s.roll_no && s.roll_no.toLowerCase().includes(term)) ||
      (s.admission_no && s.admission_no.toLowerCase().includes(term))
    );
  });

  return (
    <div className="flex h-screen bg-gray-50/50 font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="bg-white px-8 py-6 flex flex-col gap-6 sticky top-0 z-10 shrink-0 shadow-sm border-b border-gray-200">
          <div className="flex flex-wrap justify-between items-center gap-4">
            <div className="flex items-center gap-4">
              <div className="bg-indigo-50 p-3 rounded-2xl">
                <GraduationCap className="w-7 h-7 text-indigo-600" />
              </div>
              <div>
                <h1 className="m-0 text-2xl font-bold text-gray-900 tracking-tight">Students Directory</h1>
                <p className="m-0 text-sm text-gray-500 mt-0.5 font-medium">Manage student master records and enrollments</p>
              </div>
            </div>
          </div>
          
          {/* Tabs */}
          <div className="flex items-center gap-6 border-b border-gray-200">
            <button 
              onClick={() => setActiveTab('directory')}
              className={`pb-3 text-sm font-bold border-b-2 flex items-center gap-2 transition-colors ${activeTab === 'directory' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            >
              <Users className="w-4 h-4" />
              Main Directory
            </button>
            <button 
              onClick={() => setActiveTab('forms')}
              className={`pb-3 text-sm font-bold border-b-2 flex items-center gap-2 transition-colors ${activeTab === 'forms' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            >
              <LinkIcon className="w-4 h-4" />
              Public Forms
            </button>
            <button 
              onClick={() => setActiveTab('pending')}
              className={`pb-3 text-sm font-bold border-b-2 flex items-center gap-2 transition-colors ${activeTab === 'pending' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            >
              <Inbox className="w-4 h-4" />
              Pending Requests
            </button>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-8 relative">
          
          {activeTab === 'directory' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <div className="relative group w-full max-w-xl">
                  <span className="absolute inset-y-0 left-0 pl-4 flex items-center text-gray-400 group-focus-within:text-indigo-500 transition-colors">
                    <Search className="w-4 h-4" />
                  </span>
                  <input
                    type="text"
                    placeholder="Search students by name, email, roll no, or admission no..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-11 pr-4 py-3 border border-gray-200 rounded-2xl text-sm text-gray-900 outline-none transition-all placeholder:text-gray-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/5 shadow-sm bg-white"
                  />
                </div>
                <div className="flex gap-3">
                  <button 
                    className="px-5 py-2.5 bg-white text-gray-700 border border-gray-200 rounded-xl text-sm font-bold transition-all hover:bg-gray-50 flex items-center justify-center gap-2.5 shadow-sm"
                    onClick={() => setShowExportModal(true)}
                  >
                    <Download className="w-4 h-4" />
                    Export
                  </button>
                  <button 
                    className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-bold transition-all hover:bg-indigo-700 flex items-center justify-center gap-2.5 shadow-lg shadow-indigo-100"
                    onClick={handleAdd}
                  >
                    <Plus className="w-4 h-4" strokeWidth={3} />
                    Add Student
                  </button>
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-sm text-gray-700 min-w-[900px]">
                    <thead>
                      <tr className="bg-gray-50/50 border-b border-gray-200">
                        <th className="px-6 py-4 font-bold text-gray-400 text-[0.7rem] uppercase tracking-widest">Student Information</th>
                        <th className="px-6 py-4 font-bold text-gray-400 text-[0.7rem] uppercase tracking-widest">Academic Info</th>
                        <th className="px-6 py-4 font-bold text-gray-400 text-[0.7rem] uppercase tracking-widest">Contact Details</th>
                        <th className="px-6 py-4 font-bold text-gray-400 text-[0.7rem] uppercase tracking-widest">Status/Source</th>
                        <th className="px-6 py-4 font-bold text-gray-400 text-[0.7rem] uppercase tracking-widest text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {loading ? (
                        <tr>
                          <td colSpan="5" className="px-6 py-16 text-center">
                            <div className="flex flex-col items-center gap-3">
                              <div className="w-8 h-8 border-2 border-indigo-100 border-t-indigo-600 rounded-full animate-spin" />
                              <p className="text-gray-400 font-medium tracking-wide">Fetching student database...</p>
                            </div>
                          </td>
                        </tr>
                      ) : filteredStudents.length === 0 ? (
                        <tr>
                          <td colSpan="5" className="px-6 py-24 text-center">
                            <div className="flex flex-col items-center justify-center text-gray-300">
                              <div className="bg-gray-50 p-6 rounded-3xl mb-4 border border-gray-100">
                                <GraduationCap className="w-12 h-12" />
                              </div>
                              <p className="text-lg font-bold text-gray-800">No Students Found</p>
                            </div>
                          </td>
                        </tr>
                      ) : (
                        filteredStudents.map((student) => (
                          <tr key={student.id} className="hover:bg-gray-50/30 transition-colors group">
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-gray-50 border border-gray-200 text-gray-400 flex items-center justify-center shrink-0 group-hover:bg-white transition-colors">
                                  <User className="w-5 h-5" />
                                </div>
                                <div className="min-w-0">
                                  <div className="font-bold text-gray-900 truncate">{student.first_name} {student.last_name}</div>
                                  <div className="text-[0.75rem] text-gray-400 font-medium truncate">{student.email}</div>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-2">
                                <span className="bg-indigo-50 text-indigo-700 text-[0.65rem] font-black uppercase px-2 py-0.5 rounded tracking-tighter border border-indigo-100">Class {student.class_name || 'N/A'}</span>
                              </div>
                              <div className="mt-1.5 flex flex-col gap-0.5">
                                <div className="text-[0.7rem] text-gray-400 font-bold uppercase tracking-tight">Roll: <span className="text-gray-800 font-mono tracking-normal">{student.roll_no || '—'}</span></div>
                                <div className="text-[0.7rem] text-gray-400 font-bold uppercase tracking-tight">Adm: <span className="text-gray-800 font-mono tracking-normal">{student.admission_no || '—'}</span></div>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              {student.mobile_numbers && student.mobile_numbers.length > 0 ? (
                                <div className="flex flex-wrap gap-1.5 max-w-[200px]">
                                  {student.mobile_numbers.map((mobile, index) => (
                                    <span key={index} className="text-[0.7rem] font-bold text-gray-500 bg-gray-100/80 px-2 py-0.5 rounded-lg border border-gray-200/50">{mobile}</span>
                                  ))}
                                </div>
                              ) : (
                                <span className="text-gray-300 italic text-[0.75rem]">No phone provided</span>
                              )}
                            </td>
                            <td className="px-6 py-4">
                              <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[0.65rem] font-bold uppercase tracking-widest border ${student.submitted_via_form ? 'bg-amber-50 text-amber-700 border-amber-100' : 'bg-green-50 text-green-700 border-green-100'}`}>
                                <div className={`w-1.5 h-1.5 rounded-full ${student.submitted_via_form ? 'bg-amber-400' : 'bg-green-400'}`} />
                                {student.submitted_via_form ? 'Public Form' : 'Staff Added'}
                              </div>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button 
                                  className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all"
                                  onClick={() => handleEdit(student)}
                                >
                                  <Pencil className="w-4 h-4" />
                                </button>
                                <button 
                                  className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all"
                                  onClick={() => handleDelete(student.id)}
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                              <MoreVertical className="w-4 h-4 text-gray-300 group-hover:hidden ml-auto" />
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'forms' && <FormLinksTab />}
          {activeTab === 'pending' && <PendingRequestsTab />}

        </main>
      </div>

      {showForm && (
        <StudentFormModal
          student={editingStudent}
          onClose={() => setShowForm(false)}
          onSaved={loadStudents}
        />
      )}

      {showExportModal && (
        <ExportConfigModal
          students={filteredStudents}
          onClose={() => setShowExportModal(false)}
        />
      )}
    </div>
  );
}
