const BAR_DATA = [
  { month: 'Oct', enrolled: 85, passed: 72 },
  { month: 'Nov', enrolled: 90, passed: 80 },
  { month: 'Dec', enrolled: 78, passed: 65 },
  { month: 'Jan', enrolled: 95, passed: 88 },
  { month: 'Feb', enrolled: 102, passed: 94 },
  { month: 'Mar', enrolled: 110, passed: 105 },
];
const MAX = 120;

export default function ReportsChartWidget({ widget }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.02)] font-sans h-[380px] flex flex-col">
      <div className="px-5 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
        <h3 className="m-0 text-[1.05rem] font-bold text-gray-900">{widget.display_name}</h3>
        <span className="bg-purple-100 text-purple-700 px-2.5 py-0.5 rounded-full text-[0.6875rem] font-bold uppercase tracking-wider">Chart</span>
      </div>
      <div className="flex justify-end gap-5 px-5 pt-4">
        <div className="flex items-center gap-1.5 text-xs text-gray-500 font-medium tracking-wide"><span className="w-2.5 h-2.5 rounded-full bg-indigo-200" /> Enrolled</div>
        <div className="flex items-center gap-1.5 text-xs text-gray-500 font-medium tracking-wide"><span className="w-2.5 h-2.5 rounded-full bg-indigo-600" /> Passed</div>
      </div>
      <div className="flex-1 flex items-end justify-between px-5 pt-6 pb-2 h-40">
        {BAR_DATA.map((d) => (
          <div key={d.month} className="flex flex-col items-center gap-2 h-full justify-end flex-1">
            <div className="flex items-end gap-1 md:gap-1.5 h-full w-full justify-center">
              <div
                className="w-4 md:w-5 bg-indigo-200 rounded-t-sm transition-all hover:opacity-80"
                style={{ height: `${(d.enrolled / MAX) * 100}%` }}
                title={`Enrolled: ${d.enrolled}`}
              />
              <div
                className="w-4 md:w-5 bg-indigo-600 rounded-t-sm transition-all hover:opacity-80"
                style={{ height: `${(d.passed / MAX) * 100}%` }}
                title={`Passed: ${d.passed}`}
              />
            </div>
            <div className="text-[0.6875rem] text-gray-400 font-bold uppercase tracking-wider">{d.month}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-3 border-t border-gray-100 bg-gray-50/50 mt-1">
        <div className="p-3 text-center border-r border-gray-100">
          <span className="block text-[1.15rem] font-bold text-gray-900 mb-0.5">560</span>
          <span className="block text-[0.625rem] text-gray-500 font-bold uppercase tracking-wider">Total Enrolled</span>
        </div>
        <div className="p-3 text-center border-r border-gray-100">
          <span className="block text-[1.15rem] font-bold text-gray-900 mb-0.5">504</span>
          <span className="block text-[0.625rem] text-gray-500 font-bold uppercase tracking-wider">Total Passed</span>
        </div>
        <div className="p-3 text-center">
          <span className="block text-[1.15rem] font-bold text-emerald-600 mb-0.5">90%</span>
          <span className="block text-[0.625rem] text-gray-500 font-bold uppercase tracking-wider">Pass Rate</span>
        </div>
      </div>
    </div>
  );
}
