import { useAuthStore } from '../store/authStore';

/**
 * Renders children only if the user has the required permission.
 * @param {string} permission - e.g. "students:read"
 * @param {ReactNode} fallback - optional fallback UI (default: nothing)
 */
export default function PermissionGuard({ permission, children, fallback = null }) {
  const { hasPermission } = useAuthStore();
  return hasPermission(permission) ? children : fallback;
}
