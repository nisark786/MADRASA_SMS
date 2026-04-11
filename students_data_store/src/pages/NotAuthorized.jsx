import { Link } from 'react-router-dom';

export default function NotAuthorized() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-3.5 bg-gray-50 text-gray-900 font-sans">
      <div className="text-4xl">🔒</div>
      <h1 className="text-xl font-bold text-gray-900">Access Denied</h1>
      <p className="text-gray-500 max-w-[380px] text-center text-sm leading-relaxed">
        You don't have permission to view this page. Contact your administrator to request access.
      </p>
      <Link to="/dashboard" className="mt-2 px-5 py-2.5 bg-indigo-600 rounded-lg text-white no-underline font-semibold text-sm">
        ← Back to Dashboard
      </Link>
    </div>
  );
}
