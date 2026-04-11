const MOCK_STATS = [
  { label: 'Total Students', value: '1,248', icon: '👨‍🎓', trend: '+12%', color: 'bg-indigo-50 border-indigo-100 text-indigo-700' },
  { label: 'Active',         value: '1,105', icon: '✅',     trend: '+5%',  color: 'bg-emerald-50 border-emerald-100 text-emerald-700' },
  { label: 'Inactive',       value: '143',   icon: '⏸️',    trend: '-2%',  color: 'bg-orange-50 border-orange-100 text-orange-700' },
  { label: 'New This Month', value: '47',    icon: '🆕',     trend: '+18%', color: 'bg-purple-50 border-purple-100 text-purple-700' },
];

export default function StudentStatsCard({ widget }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.02)] font-sans h-full flex flex-col">
      <div className="px-5 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
        <h3 className="m-0 text-[1.05rem] font-bold text-gray-900">{widget.display_name}</h3>
        <span className="bg-indigo-100 text-indigo-700 px-2.5 py-0.5 rounded-full text-[0.6875rem] font-bold uppercase tracking-wider">Overview</span>
      </div>
      <div className="p-5 grid grid-cols-2 md:grid-cols-4 gap-4 flex-1">
        {MOCK_STATS.map((s) => (
          <div key={s.label} className={`flex flex-col p-4 rounded-xl border ${s.color}`}>
            <div className="text-2xl mb-1.5 opacity-90">{s.icon}</div>
            <div className="text-[1.35rem] font-bold leading-tight mb-0.5">{s.value}</div>
            <div className="text-[0.75rem] font-medium opacity-80 uppercase tracking-wide">{s.label}</div>
            <div className={`text-xs font-bold mt-2 ${s.trend.startsWith('+') ? 'text-emerald-600' : 'text-red-500'}`}>
              {s.trend}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
