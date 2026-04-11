const MOCK_LOGS = [
  { user: 'System Admin',  action: 'LOGIN',        resource: 'auth',  time: '10:54 AM' },
  { user: 'System Admin',  action: 'CREATE_ROLE',  resource: 'roles', time: '10:52 AM' },
  { user: 'System Admin',  action: 'CREATE_USER',  resource: 'users', time: '10:51 AM' },
  { user: 'System Admin',  action: 'CREATE_USER',  resource: 'users', time: '10:50 AM' },
  { user: 'System Admin',  action: 'LOGIN',        resource: 'auth',  time: 'Yesterday' },
];

const ACTION_COLORS = {
  LOGIN:       'bg-blue-100 text-blue-700',
  CREATE_USER: 'bg-emerald-100 text-emerald-700',
  CREATE_ROLE: 'bg-emerald-100 text-emerald-700',
  UPDATE_USER: 'bg-orange-100 text-orange-700',
  UPDATE_ROLE: 'bg-orange-100 text-orange-700',
  DELETE_USER: 'bg-red-100 text-red-700',
  DELETE_ROLE: 'bg-red-100 text-red-700',
};

const DOT_COLORS = {
  LOGIN:       'bg-blue-500',
  CREATE_USER: 'bg-emerald-500',
  CREATE_ROLE: 'bg-emerald-500',
  UPDATE_USER: 'bg-orange-500',
  UPDATE_ROLE: 'bg-orange-500',
  DELETE_USER: 'bg-red-500',
  DELETE_ROLE: 'bg-red-500',
};

export default function AuditLogWidget({ widget }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.02)] font-sans h-full flex flex-col">
      <div className="px-5 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
        <h3 className="m-0 text-[1.05rem] font-bold text-gray-900">{widget.display_name}</h3>
        <span className="bg-gray-800 text-white px-2.5 py-0.5 rounded-full text-[0.6875rem] font-bold uppercase tracking-wider">Admin</span>
      </div>
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-1">
        {MOCK_LOGS.map((log, i) => (
          <div key={i} className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-gray-50/80 transition-colors border border-transparent hover:border-gray-100 group">
            <div className={`w-2 h-2 rounded-full shadow-[0_0_0_4px_white] ${DOT_COLORS[log.action] || 'bg-gray-400'}`} />
            <div className="flex-1 flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-gray-900 text-[0.8125rem]">{log.user}</span>
              <span className={`text-[0.6rem] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${ACTION_COLORS[log.action] || 'bg-gray-100 text-gray-600'}`}>{log.action}</span>
              <span className="text-gray-500 text-[0.8125rem]">on {log.resource}</span>
            </div>
            <span className="text-xs text-gray-400 whitespace-nowrap group-hover:text-gray-600 transition-colors font-medium">{log.time}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
