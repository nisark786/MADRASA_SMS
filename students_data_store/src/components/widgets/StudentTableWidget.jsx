import { useState } from 'react';

const MOCK_STUDENTS = [
  { id: 1, name: 'Alice Johnson',  roll: 'S001', class: '10-A', grade: 'A',  phone: '555-0101', status: 'Active' },
  { id: 2, name: 'Bob Smith',      roll: 'S002', class: '10-B', grade: 'B+', phone: '555-0102', status: 'Active' },
  { id: 3, name: 'Carol White',    roll: 'S003', class: '11-A', grade: 'A+', phone: '555-0103', status: 'Active' },
  { id: 4, name: 'David Brown',    roll: 'S004', class: '11-B', grade: 'C',  phone: '555-0104', status: 'Inactive' },
  { id: 5, name: 'Eva Martinez',   roll: 'S005', class: '12-A', grade: 'A',  phone: '555-0105', status: 'Active' },
  { id: 6, name: 'Frank Lee',      roll: 'S006', class: '12-B', grade: 'B',  phone: '555-0106', status: 'Active' },
  { id: 7, name: 'Grace Kim',      roll: 'S007', class: '10-A', grade: 'A+', phone: '555-0107', status: 'Active' },
  { id: 8, name: 'Henry Wilson',   roll: 'S008', class: '10-C', grade: 'D',  phone: '555-0108', status: 'Inactive' },
];

export default function StudentTableWidget({ widget }) {
  const [search, setSearch] = useState('');
  const filtered = MOCK_STUDENTS.filter((s) =>
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    s.roll.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.02)] font-sans h-full flex flex-col">
      <div className="px-5 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50 shrink-0">
        <h3 className="m-0 text-[1.05rem] font-bold text-gray-900">{widget.display_name}</h3>
        <span className="bg-blue-100 text-blue-700 px-2.5 py-0.5 rounded-full text-[0.6875rem] font-bold uppercase tracking-wider">Table</span>
      </div>
      <div className="p-3 border-b border-gray-100 flex justify-between items-center bg-white shrink-0">
        <input
          id="student-search"
          className="w-full max-w-[280px] px-3 py-1.5 border border-gray-200 rounded-md text-[0.8125rem] text-gray-900 outline-none transition-all placeholder:text-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 bg-gray-50/50"
          type="text"
          placeholder="🔍 Search by name or roll..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <span className="text-[0.75rem] font-semibold text-gray-400 bg-gray-50 px-2.5 py-1 rounded-full border border-gray-200">{filtered.length} records</span>
      </div>
      <div className="flex-1 overflow-x-auto overflow-y-auto">
        <table className="w-full text-left border-collapse text-sm text-gray-700 min-w-[500px]">
          <thead className="bg-gray-50/80 sticky top-0 border-b border-gray-200">
            <tr className="text-[0.7rem] uppercase tracking-wider text-gray-500 font-semibold">
              <th className="px-4 py-3">Roll No</th><th className="px-4 py-3">Name</th><th className="px-4 py-3">Class</th>
              <th className="px-4 py-3">Grade</th><th className="px-4 py-3">Phone</th><th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((s) => (
              <tr key={s.id} className="hover:bg-gray-50/50 transition-colors">
                <td className="px-4 py-3"><code className="bg-gray-50 text-gray-600 px-1.5 py-0.5 rounded text-[0.75rem] border border-gray-200 font-mono">{s.roll}</code></td>
                <td className="px-4 py-3 text-gray-900 font-medium whitespace-nowrap">{s.name}</td>
                <td className="px-4 py-3 text-gray-500">{s.class}</td>
                <td className="px-4 py-3"><span className={`inline-block px-2 py-0.5 rounded text-[0.75rem] font-bold ${s.grade.startsWith('A') ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : s.grade.startsWith('B') ? 'bg-blue-50 text-blue-700 border border-blue-200' : s.grade.startsWith('C') ? 'bg-orange-50 text-orange-700 border border-orange-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>{s.grade}</span></td>
                <td className="px-4 py-3 text-gray-500">{s.phone}</td>
                <td className="px-4 py-3">
                  <span className={`inline-block px-1.5 py-0.5 rounded text-[0.65rem] font-bold uppercase tracking-wider border ${s.status === 'Active' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-gray-50 text-gray-500 border-gray-200'}`}>
                    {s.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
