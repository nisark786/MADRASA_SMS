import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Download, FileText, FileSpreadsheet, XCircle } from 'lucide-react';

const AVAILABLE_FIELDS = [
  { id: 'first_name', label: 'First Name' },
  { id: 'last_name', label: 'Last Name' },
  { id: 'email', label: 'Email Address' },
  { id: 'phone', label: 'Phone Number' }, // Mapped from mobile_numbers array
  { id: 'class_name', label: 'Class/Grade' },
  { id: 'roll_no', label: 'Roll Number' },
  { id: 'admission_no', label: 'Admission Number' },
  { id: 'address', label: 'Address' },
  { id: 'city', label: 'City' },
  { id: 'state', label: 'State' },
  { id: 'zip_code', label: 'Zip Code' },
  { id: 'date_of_birth', label: 'Date of Birth' },
  { id: 'enrollment_date', label: 'Enrollment Date' },
];

export default function ExportConfigModal({ onClose, students }) {
  const [format, setFormat] = useState('pdf'); // 'pdf' or 'csv'
  const [selectedFields, setSelectedFields] = useState([
    'first_name', 'last_name', 'email', 'class_name', 'roll_no'
  ]);
  const navigate = useNavigate();

  const toggleField = (fieldId) => {
    setSelectedFields(prev => 
      prev.includes(fieldId) 
        ? prev.filter(f => f !== fieldId)
        : [...prev, fieldId]
    );
  };

  const selectAll = () => setSelectedFields(AVAILABLE_FIELDS.map(f => f.id));
  const clearAll = () => setSelectedFields([]);

  const executeExport = () => {
    if (selectedFields.length === 0) return alert('Please select at least one field to export.');

    const fieldsToInclude = AVAILABLE_FIELDS.filter(f => selectedFields.includes(f.id));

    if (format === 'csv') {
      // Generate CSV Blob
      const headers = fieldsToInclude.map(f => f.label).join(',');
      const rows = students.map(student => {
        return fieldsToInclude.map(f => {
          let val = student[f.id];
          if (f.id === 'phone') val = student.mobile_numbers?.[0] || '';
          if (val === null || val === undefined) val = '';
          // Escape quotes and wrap in quotes for CSV safety
          const escaped = String(val).replace(/"/g, '""');
          return `"${escaped}"`;
        }).join(',');
      });

      const csvContent = [headers, ...rows].join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `Students_Export_${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      onClose();
    } else {
      // Navigate to PDF Print page, passing data via state
      // Note: For large datasets, localStorage might be safer than history state if it exceeds size limits,
      // but React Router state usually handles a few thousand records fine in memory.
      navigate('/admin/students/report', { 
        state: { 
          students, 
          fields: fieldsToInclude 
        } 
      });
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 backdrop-blur-sm p-4">
      <div className="bg-white w-full max-w-2xl rounded-3xl p-8 shadow-2xl relative flex flex-col max-h-[90vh]">
        <button onClick={onClose} className="absolute top-6 right-6 text-gray-400 hover:text-gray-900">
          <XCircle className="w-6 h-6" />
        </button>
        
        <h2 className="text-2xl font-bold mb-2 text-gray-900">Export Students Data</h2>
        <p className="text-gray-500 text-sm mb-6">Customize the columns and format for your export file.</p>

        <div className="flex flex-col md:flex-row gap-8 overflow-hidden">
          {/* Format Selection Column */}
          <div className="w-full md:w-1/3 flex flex-col gap-4 border-b md:border-b-0 md:border-r border-gray-100 pb-6 md:pb-0 md:pr-6 shrink-0">
            <h3 className="font-bold text-gray-700 text-sm uppercase tracking-wider">1. Select Format</h3>
            
            <label className={`flex flex-col p-4 rounded-2xl border-2 cursor-pointer transition-colors ${format === 'pdf' ? 'border-indigo-600 bg-indigo-50/50' : 'border-gray-100 hover:border-gray-200 bg-white'}`}>
              <div className="flex items-center justify-between mb-2">
                <FileText className={`w-6 h-6 ${format === 'pdf' ? 'text-indigo-600' : 'text-gray-400'}`} />
                <input type="radio" value="pdf" checked={format === 'pdf'} onChange={() => setFormat('pdf')} className="text-indigo-600 focus:ring-0" />
              </div>
              <span className="font-bold text-gray-900">PDF Report</span>
              <span className="text-xs text-gray-500 mt-1">Formal document layout, perfect for printing.</span>
            </label>

            <label className={`flex flex-col p-4 rounded-2xl border-2 cursor-pointer transition-colors ${format === 'csv' ? 'border-indigo-600 bg-indigo-50/50' : 'border-gray-100 hover:border-gray-200 bg-white'}`}>
              <div className="flex items-center justify-between mb-2">
                <FileSpreadsheet className={`w-6 h-6 ${format === 'csv' ? 'text-indigo-600' : 'text-gray-400'}`} />
                <input type="radio" value="csv" checked={format === 'csv'} onChange={() => setFormat('csv')} className="text-indigo-600 focus:ring-0" />
              </div>
              <span className="font-bold text-gray-900">CSV Excel</span>
              <span className="text-xs text-gray-500 mt-1">Raw spreadsheet data for Excel tracking.</span>
            </label>
          </div>

          {/* Fields Selection Column */}
          <div className="w-full md:w-2/3 flex flex-col flex-1 min-h-0">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-gray-700 text-sm uppercase tracking-wider">2. Select Columns</h3>
              <div className="flex gap-3 text-xs font-bold text-indigo-600">
                <button onClick={selectAll} className="hover:underline">Select All</button>
                <button onClick={clearAll} className="hover:underline">Clear</button>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-3 overflow-y-auto pr-2 pb-2 flex-1">
              {AVAILABLE_FIELDS.map(f => (
                <label key={f.id} className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${selectedFields.includes(f.id) ? 'bg-white border-indigo-200 shadow-sm' : 'bg-gray-50 border-transparent hover:bg-gray-100'}`}>
                  <input 
                    type="checkbox"
                    checked={selectedFields.includes(f.id)}
                    onChange={() => toggleField(f.id)}
                    className="rounded text-indigo-600 focus:ring-0 cursor-pointer w-4 h-4"
                  />
                  <span className={`text-sm ${selectedFields.includes(f.id) ? 'font-bold text-indigo-900' : 'font-medium text-gray-600'}`}>{f.label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex justify-end gap-3 pt-6 mt-6 border-t border-gray-100 shrink-0">
          <button onClick={onClose} className="px-6 py-3 rounded-xl text-sm font-bold text-gray-500 hover:bg-gray-100 transition-colors">
            Cancel
          </button>
          <button 
            onClick={executeExport}
            className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg shadow-indigo-200 transition-all active:scale-95"
          >
            <Download className="w-4 h-4" />
            {format === 'pdf' ? 'Generate PDF' : 'Download CSV'}
          </button>
        </div>
      </div>
    </div>
  );
}
