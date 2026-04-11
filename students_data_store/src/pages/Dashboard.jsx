import { useAuthStore } from '../store/authStore';
import Sidebar from '../components/layout/Sidebar';
import { LayoutDashboard, Construction } from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuthStore();

  return (
    <div className="flex min-h-screen bg-gray-50/50 font-sans">
      <Sidebar />
      <main className="flex-1 p-8 md:p-12 overflow-y-auto min-w-0">
        <div className="flex items-start justify-between mb-8 max-w-7xl mx-auto">
          <div>
            <div className="flex items-center gap-2.5 mb-2">
              <div className="bg-indigo-600 p-2 rounded-xl">
                <LayoutDashboard className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 leading-tight tracking-tight">System Dashboard</h1>
            </div>
            <p className="text-sm text-gray-500 font-medium ml-1">
              Welcome back, <strong className="text-gray-900 font-bold">{user?.first_name} {user?.last_name}</strong>
            </p>
          </div>
          <div className="bg-white border border-gray-200 rounded-full px-5 py-2 text-[0.65rem] font-black text-gray-400 shadow-sm uppercase tracking-widest border-dashed">
            Pending Configuration
          </div>
        </div>

        <div className="flex flex-col items-center justify-center min-h-[60vh] max-w-7xl mx-auto">
          <div className="bg-white p-10 rounded-[2.5rem] border border-gray-100 shadow-[0_20px_50px_rgba(0,0,0,0.03)] flex flex-col items-center gap-6 group hover:shadow-indigo-500/5 transition-all duration-500">
            <div className="relative">
              <div className="absolute inset-0 bg-indigo-500/20 rounded-full blur-2xl group-hover:bg-indigo-500/30 transition-all duration-500" />
              <div className="relative bg-gray-900 p-6 rounded-3xl shadow-2xl">
                <Construction className="w-12 h-12 text-indigo-400" strokeWidth={1.5} />
              </div>
            </div>
            
            <div className="text-center flex flex-col gap-2">
              <h3 className="text-xl font-bold text-gray-900 tracking-tight">Dashboard Under Assembly</h3>
              <p className="text-sm text-gray-400 font-medium max-w-[320px] leading-relaxed">
                We are currently refining the analytics and metric visualizations for this section.
              </p>
            </div>

            <div className="flex gap-2">
              <div className="w-2 h-2 rounded-full bg-indigo-600 animate-bounce [animation-delay:-0.3s]" />
              <div className="w-2 h-2 rounded-full bg-indigo-600 animate-bounce [animation-delay:-0.15s]" />
              <div className="w-2 h-2 rounded-full bg-indigo-600 animate-bounce" />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
