import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

/** Requires login. Optionally requires a specific permission. */
export default function ProtectedRoute({ children, permission }) {
  const { user, hasPermission } = useAuthStore();
  if (!user) return <Navigate to="/login" replace />;
  if (permission && !hasPermission(permission)) return <Navigate to="/not-authorized" replace />;
  return children;
}
