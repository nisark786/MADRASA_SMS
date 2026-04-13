import { NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { 
  Home, 
  Users, 
  ShieldCheck, 
  ListTodo, 
  GraduationCap, 
  LogOut,
  Mail,
  User as UserIcon,
  FileText
} from 'lucide-react';

const NAV_ITEMS = [
  { to: '/dashboard',           label: 'Dashboard',    icon: Home, permission: null },
  { to: '/admin/students',      label: 'Students',     icon: GraduationCap, permission: 'students:read' },
  { to: '/admin/users',         label: 'Users',        icon: Users, permission: 'admin:manage_users' },
  { to: '/admin/roles',         label: 'Roles',        icon: ShieldCheck, permission: 'admin:manage_roles' },
  { to: '/admin/audit-logs',    label: 'Audit Logs',   icon: FileText, permission: 'admin:view_audit' },
  { to: '/admin/emails',        label: 'Email History',icon: Mail, permission: 'admin:manage_users' },
  { to: '/profile',             label: 'My Profile',   icon: UserIcon, permission: null },
];

export default function Sidebar() {
  const { user, permissions, logout, hasPermission } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <aside className="w-64 min-h-screen bg-white border-r border-gray-200 flex flex-col p-6 sticky top-0 h-screen shrink-0 shadow-[4px_0_24px_rgba(0,0,0,0.02)]" id="sidebar">
      <div className="flex items-center gap-3 px-1.5 mb-8">
        <div className="bg-indigo-600 p-2 rounded-xl shadow-lg shadow-indigo-200">
          <GraduationCap className="w-6 h-6 text-white" />
        </div>
        <div>
          <div className="font-bold text-[1rem] text-gray-900 tracking-tight">Students DS</div>
          <div className="text-[0.7rem] text-gray-400 font-medium uppercase tracking-widest leading-none mt-1">v1.2.0</div>
        </div>
      </div>

      <nav className="flex-1 flex flex-col gap-1.5">
        {NAV_ITEMS.map(({ to, label, icon: Icon, permission }) => {
          if (permission && !hasPermission(permission)) return null;
          return (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl no-underline text-sm font-semibold transition-all duration-200 ${
                  isActive 
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-100 translate-x-1' 
                    : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
              id={`nav-${label.toLowerCase().replace(/\s/g, '-')}`}
            >
              {({ isActive }) => (
                <>
                  <Icon className={`w-[18px] h-[18px] shrink-0 ${isActive ? 'text-white' : 'text-gray-400 group-hover:text-gray-600'}`} strokeWidth={2.2} />
                  <span>{label}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="border-t border-gray-100 pt-6 mt-auto flex flex-col gap-4">
        <div className="flex items-center gap-3 px-1 group cursor-pointer">
          <div className="w-10 h-10 rounded-xl bg-gray-50 border border-gray-200 text-gray-400 flex items-center justify-center transition-colors group-hover:border-indigo-200 group-hover:bg-indigo-50 group-hover:text-indigo-600">
            <UserIcon className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <div className="text-[0.875rem] font-bold text-gray-900 truncate">{user?.first_name} {user?.last_name}</div>
            <div className="text-[0.7rem] text-gray-400 font-medium truncate">{user?.email}</div>
          </div>
        </div>
        <div className="text-[0.7rem] font-bold text-indigo-500/80 bg-indigo-50/50 px-2 py-1 rounded-md w-fit ml-1 border border-indigo-100/50">
          {permissions.length} PERMISSION{permissions.length !== 1 ? 'S' : ''}
        </div>
        <button 
          className="w-full px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-gray-600 text-[0.8125rem] font-bold cursor-pointer transition-all flex items-center justify-center gap-2 hover:bg-red-50 hover:border-red-100 hover:text-red-600" 
          id="logout-btn" 
          onClick={handleLogout}
        >
          <LogOut className="w-4 h-4" strokeWidth={2.5} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
